"""Dataset MURA pour la détection de fractures osseuses
Structure réelle:
- train_labeled_studies.csv: "chemin/vers/study/,label"
- Les images sont dans study/*.png
"""

import pandas as pd
import numpy as np
from PIL import Image
import torch
from torch.utils.data import Dataset
from pathlib import Path
from typing import Tuple, Optional, Dict, List
import cv2
import os

from .transforms import get_transforms
from config.settings import settings


class MURADataset(Dataset):
    """
    Dataset MURA (Musculoskeletal Radiographs)
    Classification binaire: Normal (0) vs Anormal (1)
    
    Le CSV contient des lignes comme:
    "MURA-v1.1/train/XR_WRIST/patient00010/study1_positive/,1"
    """
    
    def __init__(
        self,
        csv_path: Path,
        data_dir: Path,
        mode: str = 'train',
        image_size: int = 224,
        use_metadata: bool = False
    ):
        """
        Args:
            csv_path: Chemin vers train_labeled_studies.csv ou valid_labeled_studies.csv
            data_dir: Répertoire racine des images MURA (ex: data/MURA-v1.1)
            mode: 'train', 'val', ou 'test'
            image_size: Taille de redimensionnement
            use_metadata: Utiliser les métadonnées (patient, étude)
        """
        self.data_dir = Path(data_dir).parent
        self.mode = mode
        self.image_size = image_size
        self.use_metadata = use_metadata
        
        # Charger le CSV
        # Format: "path/to/study/,label"
        self.df = pd.read_csv(csv_path, header=None, names=['study_path', 'label'])
        
        # Nettoyer les chemins (enlever les guillemets si présents)
        self.df['study_path'] = self.df['study_path'].str.strip().str.strip('"')
        self.df['label'] = self.df['label'].astype(int)
        
        # Construire la liste de toutes les images
        self.image_paths = []
        self.labels = []
        
        for idx, row in self.df.iterrows():
            study_path = row['study_path']
            # print(f"Processing study: {study_path} with label {row['label']}")
            label = row['label']
            
            # Le chemin dans le CSV est relatif à data_dir
            full_study_path = self.data_dir / study_path
            
            if not full_study_path.exists():
                print(f"Attention: Dossier non trouvé - {full_study_path}")
                continue
            
            # Lister toutes les images .png dans le dossier study
            image_files = list(full_study_path.glob("*.png")) + \
                         list(full_study_path.glob("*.PNG")) + \
                         list(full_study_path.glob("*.jpg")) + \
                         list(full_study_path.glob("*.jpeg"))
            
            for img_file in image_files:
                # Stocker le chemin relatif à data_dir
                rel_path = img_file.relative_to(self.data_dir)
                self.image_paths.append(str(rel_path))
                self.labels.append(label)
        
        self.labels = np.array(self.labels)
        
        # Transforms
        self.transform = get_transforms(mode, image_size)
        
        print(f"[MURA] {mode} dataset: {len(self.image_paths)} images, {len(self.df)} études")
        print(f"[MURA] Classes - Normal (0): {sum(self.labels == 0)}, "
              f"Anormal (1): {sum(self.labels == 1)}")
    
    def _load_image(self, path: str) -> np.ndarray:
        """Charge une image depuis le chemin relatif"""
        full_path = self.data_dir / path
        
        if not full_path.exists():
            raise FileNotFoundError(f"Image non trouvée: {full_path}")
        
        # Charger avec PIL
        img = Image.open(full_path).convert('RGB')
        return np.array(img)
    
    def _extract_metadata(self, path: str) -> Dict[str, str]:
        """Extrait les métadonnées du patient, body part, et étude"""
        parts = Path(path).parts
        # Format: train/XR_WRIST/patient00010/study1_positive/image1.png
        metadata = {
            'split': parts[0] if len(parts) > 0 else '',
            'body_part': parts[1] if len(parts) > 1 else '',
            'patient': parts[2] if len(parts) > 2 else '',
            'study': parts[3] if len(parts) > 3 else '',
            'is_positive': 'positive' in parts[3] if len(parts) > 3 else False
        }
        return metadata
    
    def __len__(self) -> int:
        return len(self.image_paths)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        # Charger l'image
        img_path = self.image_paths[idx]
        img_array = self._load_image(img_path)
        
        # Appliquer les transformations
        if self.transform:
            transformed = self.transform(image=img_array)
            img_tensor = transformed['image']
        else:
            from torchvision import transforms
            img_tensor = transforms.ToTensor()(img_array)
        
        # Label
        label = torch.tensor(self.labels[idx], dtype=torch.float32)
        
        if self.use_metadata:
            metadata = self._extract_metadata(img_path)
            return img_tensor, label, metadata
        
        return img_tensor, label


class MURAByStudyDataset(Dataset):
    """
    Version qui charge toutes les images d'une étude ensemble
    Utile pour la validation où la prédiction se fait par étude
    """
    
    def __init__(
        self,
        csv_path: Path,
        data_dir: Path,
        mode: str = 'val',
        image_size: int = 224
    ):
        self.data_dir = Path(data_dir)
        self.image_size = image_size
        self.mode = mode
        
        # Charger le CSV
        self.df = pd.read_csv(csv_path, header=None, names=['study_path', 'label'])
        self.df['study_path'] = self.df['study_path'].str.strip().str.strip('"')
        self.df['label'] = self.df['label'].astype(int)
        
        # Pour chaque étude, collecter toutes les images
        self.studies = []
        
        for idx, row in self.df.iterrows():
            study_path = row['study_path']
            label = row['label']
            full_study_path = self.data_dir / study_path
            
            if full_study_path.exists():
                image_files = list(full_study_path.glob("*.png")) + \
                             list(full_study_path.glob("*.PNG"))
                
                rel_paths = [str(f.relative_to(self.data_dir)) for f in image_files]
                
                self.studies.append({
                    'study_path': study_path,
                    'label': label,
                    'image_paths': rel_paths,
                    'num_images': len(rel_paths)
                })
        
        self.transform = get_transforms(mode, image_size)
        
        print(f"[MURA ByStudy] {len(self.studies)} études, "
              f"moyenne {np.mean([s['num_images'] for s in self.studies]):.1f} images/étude")
    
    def __len__(self) -> int:
        return len(self.studies)
    
    def __getitem__(self, idx: int) -> Tuple[List[torch.Tensor], torch.Tensor]:
        study = self.studies[idx]
        
        images = []
        for img_path in study['image_paths']:
            full_path = self.data_dir / img_path
            img = Image.open(full_path).convert('RGB')
            img_array = np.array(img)
            transformed = self.transform(image=img_array)
            images.append(transformed['image'])
        
        label = torch.tensor(study['label'], dtype=torch.float32)
        
        return images, label, study['study_path']


class MURABalancedSampler(torch.utils.data.Sampler):
    """Sampler équilibré pour les classes déséquilibrées"""
    
    def __init__(self, dataset: MURADataset, batch_size: int):
        self.dataset = dataset
        self.batch_size = batch_size
        
        # Indices par classe
        self.pos_indices = np.where(dataset.labels == 1)[0]
        self.neg_indices = np.where(dataset.labels == 0)[0]
        
        self.num_pos = len(self.pos_indices)
        self.num_neg = len(self.neg_indices)
        
        print(f"[BalancedSampler] Positifs: {self.num_pos}, Négatifs: {self.num_neg}")
    
    def __iter__(self):
        # Mélanger les indices
        pos_shuffled = self.pos_indices.copy()
        neg_shuffled = self.neg_indices.copy()
        np.random.shuffle(pos_shuffled)
        np.random.shuffle(neg_shuffled)
        
        # Prendre autant de positifs que de négatifs par batch
        batch_size_half = self.batch_size // 2
        num_batches = min(len(pos_shuffled), len(neg_shuffled)) // batch_size_half
        
        for i in range(num_batches):
            pos_batch = pos_shuffled[i * batch_size_half:(i + 1) * batch_size_half]
            neg_batch = neg_shuffled[i * batch_size_half:(i + 1) * batch_size_half]
            
            batch = np.concatenate([pos_batch, neg_batch])
            np.random.shuffle(batch)
            
            for idx in batch:
                yield idx
    
    def __len__(self) -> int:
        return min(len(self.pos_indices), len(self.neg_indices)) * 2


def quick_test_mura_dataset():
    """Fonction de test rapide pour vérifier que le dataset fonctionne"""
    print("\n=== Test rapide du dataset MURA ===")
    
    # Vérifier que les fichiers existent
    if not settings.MURA_TRAIN_CSV.exists():
        print(f"❌ Fichier non trouvé: {settings.MURA_TRAIN_CSV}")
        print("Vérifiez que vous avez téléchargé MURA et que les chemins sont corrects")
        return False
    
    if not settings.MURA_DATA_DIR.exists():
        print(f"❌ Dossier non trouvé: {settings.MURA_DATA_DIR}")
        return False
    
    # Tester le dataset
    try:
        dataset = MURADataset(
            csv_path=settings.MURA_TRAIN_CSV,
            data_dir=settings.MURA_DATA_DIR,
            mode='train',
            image_size=224
        )
        
        print(f"✓ Dataset créé avec succès!")
        print(f"  - {len(dataset)} images")
        
        # Tester un élément
        img, label = dataset[0]
        print(f"  - Image shape: {img.shape}")
        print(f"  - Label: {label.item()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


if __name__ == '__main__':
    quick_test_mura_dataset()