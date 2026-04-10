#!/usr/bin/env python
"""
Script d'entraînement pour MURA (détection de fractures osseuses)
Usage: python scripts/train_mura.py
"""

import sys
from pathlib import Path

# Ajouter le parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import numpy as np
from tqdm import tqdm
import mlflow
from datetime import datetime

from config.settings import settings
from src.dataset.mura_dataset import MURADataset, MURABalancedSampler
from src.models.builder import build_model
from src.training.metrics import compute_metrics
from src.utils.logger import setup_logger
from src.utils.mlflow_utils import setup_mlflow


def train_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: str,
    scaler: torch.cuda.amp.GradScaler = None
) -> float:
    """Entraîne un epoch"""
    model.train()
    total_loss = 0.0
    
    for images, labels in tqdm(loader, desc='Training', leave=False):
        images = images.to(device)
        labels = labels.to(device).unsqueeze(1)  # (B,) -> (B, 1)
        
        optimizer.zero_grad()
        
        # Mixed precision training (si disponible)
        if scaler:
            with torch.cuda.amp.autocast():
                outputs = model(images)
                loss = criterion(outputs, labels)
            
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
        else:
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
        
        total_loss += loss.item()
    
    return total_loss / len(loader)


def validate(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: str
) -> dict:
    """Validation"""
    model.eval()
    total_loss = 0.0
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for images, labels in tqdm(loader, desc='Validation', leave=False):
            images = images.to(device)
            labels = labels.to(device).unsqueeze(1)
            
            outputs = model(images)
            loss = criterion(outputs, labels)
            total_loss += loss.item()
            
            # Probabilités
            probs = torch.sigmoid(outputs)
            all_preds.extend(probs.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    
    # Métriques
    metrics = compute_metrics(
        np.array(all_preds),
        np.array(all_labels),
        threshold=settings.THRESHOLD
    )
    metrics['loss'] = total_loss / len(loader)
    
    return metrics


def train_mura():
    """Fonction principale d'entraînement"""
    
    # Créer les répertoires
    settings.create_dirs()
    
    # Logger
    logger = setup_logger('mura_training', settings.LOG_FILE)
    logger.info("=" * 60)
    logger.info("Démarrage de l'entraînement MURA")
    logger.info(f"Device: {settings.DEVICE}")
    logger.info(f"Image size: {settings.IMAGE_SIZE}")
    logger.info(f"Batch size: {settings.BATCH_SIZE}")
    logger.info(f"Learning rate: {settings.LEARNING_RATE}")
    logger.info("=" * 60)
    
    # Vérifier que les données existent
    if not settings.MURA_TRAIN_CSV.exists():
        logger.error(f"Fichier non trouvé: {settings.MURA_TRAIN_CSV}")
        logger.error("Assurez-vous d'avoir téléchargé MURA et configuré les chemins")
        return
    
    if not settings.MURA_DATA_DIR.exists():
        logger.error(f"Dossier non trouvé: {settings.MURA_DATA_DIR}")
        return
    
    # MLflow
    setup_mlflow(settings.MLFLOW_TRACKING_URI)
    mlflow.set_experiment(settings.MLFLOW_MURA_EXPERIMENT_NAME)
    
    # Datasets
    logger.info("Chargement des datasets...")
    train_dataset = MURADataset(
        csv_path=settings.MURA_TRAIN_CSV,
        data_dir=settings.MURA_DATA_DIR,
        mode='train',
        image_size=settings.IMAGE_SIZE
    )
    
    val_dataset = MURADataset(
        csv_path=settings.MURA_VAL_CSV,
        data_dir=settings.MURA_DATA_DIR,
        mode='val',
        image_size=settings.IMAGE_SIZE
    )
    
    # DataLoaders
    # Utiliser un sampler équilibré pour le train
    train_sampler = MURABalancedSampler(train_dataset, settings.BATCH_SIZE)
    train_loader = DataLoader(
        train_dataset,
        batch_size=settings.BATCH_SIZE,
        sampler=train_sampler,
        num_workers=settings.NUM_WORKERS,
        pin_memory=True
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=settings.BATCH_SIZE,
        shuffle=False,
        num_workers=settings.NUM_WORKERS,
        pin_memory=True
    )
    
    # Modèle
    logger.info("Construction du modèle...")
    model = build_model(
        num_classes=1,
        device=settings.DEVICE,
        model_path=None  # Partir du pré-entraîné ImageNet
    )
    
    # Loss, optimizer, scheduler
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=settings.LEARNING_RATE,
        weight_decay=settings.WEIGHT_DECAY
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer,
        T_max=settings.NUM_EPOCHS
    )
    
    # Mixed precision
    scaler = torch.cuda.amp.GradScaler() if settings.DEVICE == 'cuda' else None
    
    # MLflow logging
    with mlflow.start_run(run_name=f"mura_train_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
        mlflow.log_params({
            'image_size': settings.IMAGE_SIZE,
            'batch_size': settings.BATCH_SIZE,
            'learning_rate': settings.LEARNING_RATE,
            'weight_decay': settings.WEIGHT_DECAY,
            'num_epochs': settings.NUM_EPOCHS,
            'model_name': settings.MODEL_NAME,
            'threshold': settings.THRESHOLD,
            'train_samples': len(train_dataset),
            'val_samples': len(val_dataset)
        })
        
        best_accuracy = 0.0
        
        for epoch in range(settings.NUM_EPOCHS):
            logger.info(f"\nEpoch {epoch + 1}/{settings.NUM_EPOCHS}")
            
            # Train
            train_loss = train_epoch(
                model, train_loader, criterion, optimizer,
                settings.DEVICE, scaler
            )
            
            # Validation
            val_metrics = validate(model, val_loader, criterion, settings.DEVICE)
            
            # Scheduler step
            scheduler.step()
            
            # Log MLflow
            mlflow.log_metrics({
                'train_loss': train_loss,
                'val_loss': val_metrics['loss'],
                'val_accuracy': val_metrics['accuracy'],
                'val_auc': val_metrics['auc'],
                'val_sensitivity': val_metrics['sensitivity'],
                'val_specificity': val_metrics['specificity'],
                'learning_rate': optimizer.param_groups[0]['lr']
            }, step=epoch)
            
            logger.info(
                f"Train Loss: {train_loss:.4f} | "
                f"Val Loss: {val_metrics['loss']:.4f} | "
                f"Acc: {val_metrics['accuracy']:.4f} | "
                f"AUC: {val_metrics['auc']:.4f} | "
                f"Sen: {val_metrics['sensitivity']:.4f} | "
                f"Spe: {val_metrics['specificity']:.4f}"
            )
            
            # Sauvegarder le meilleur modèle
            if val_metrics['accuracy'] > best_accuracy:
                best_accuracy = val_metrics['accuracy']
                torch.save({
                    'epoch': epoch,
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'val_metrics': val_metrics,
                    'best_accuracy': best_accuracy
                }, settings.MURA_MODEL_PATH)
                logger.info(f"✓ Meilleur modèle sauvegardé (Acc: {best_accuracy:.4f})")
        
        logger.info(f"\n✅ Entraînement terminé! Meilleure accuracy: {best_accuracy:.4f}")
        logger.info(f"Modèle sauvegardé: {settings.MURA_MODEL_PATH}")


def quick_test():
    """Test rapide pour vérifier que tout fonctionne"""
    print("\n=== Test rapide avant entraînement ===")
    
    # Vérifier les fichiers
    if not settings.MURA_TRAIN_CSV.exists():
        print(f"❌ CSV non trouvé: {settings.MURA_TRAIN_CSV}")
        print("\nTéléchargez MURA depuis: https://stanfordmlgroup.github.io/competitions/mura/")
        print("Placez les fichiers dans:", settings.MURA_DATA_DIR)
        return False
    
    # Tester le dataset
    try:
        dataset = MURADataset(
            csv_path=settings.MURA_TRAIN_CSV,
            data_dir=settings.MURA_DATA_DIR,
            mode='train',
            image_size=224
        )
        print(f"✓ Dataset chargé: {len(dataset)} images")
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


if __name__ == '__main__':
    # D'abord tester
    if quick_test():
        print("\n✅ Tout est prêt! Lancement de l'entraînement...")
        train_mura()
    else:
        print("\n❌ Veuillez corriger les problèmes ci-dessus avant de lancer l'entraînement")