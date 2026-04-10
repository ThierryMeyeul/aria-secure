#!/usr/bin/env python
"""
Script de vérification de la structure MURA
Usage: python scripts/verify_mura_structure.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from config.settings import settings


def verify_mura_structure():
    """Vérifie que la structure MURA est correcte"""
    
    print("=" * 60)
    print("Vérification de la structure MURA")
    print("=" * 60)
    
    # 1. Vérifier le dossier principal
    print(f"\n1. Dossier MURA: {settings.MURA_DATA_DIR}")
    if not settings.MURA_DATA_DIR.exists():
        print(f"   ❌ Dossier non trouvé!")
        print(f"   Créez-le et téléchargez MURA depuis https://stanfordmlgroup.github.io/competitions/mura/")
        return False
    print(f"   ✓ Dossier trouvé")
    
    # 2. Vérifier les sous-dossiers
    subdirs = ['train', 'valid']
    for subdir in subdirs:
        subpath = settings.MURA_DATA_DIR / subdir
        if subpath.exists():
            print(f"   ✓ {subdir}/ existe")
        else:
            print(f"   ⚠ {subdir}/ n'existe pas")
    
    # 3. Vérifier les CSV
    print(f"\n2. Fichiers CSV:")
    for csv_path in [settings.MURA_TRAIN_CSV, settings.MURA_VAL_CSV]:
        if csv_path.exists():
            df = pd.read_csv(csv_path, header=None)
            print(f"   ✓ {csv_path.name} - {len(df)} études")
        else:
            print(f"   ❌ {csv_path} non trouvé!")
            return False
    
    # 4. Vérifier quelques études aléatoires
    print(f"\n3. Vérification des études:")
    
    train_df = pd.read_csv(settings.MURA_TRAIN_CSV, header=None, names=['path', 'label'])
    train_df['path'] = train_df['path'].str.strip().str.strip('"')
    
    # Prendre 3 études aléatoires
    sample_studies = train_df.sample(min(3, len(train_df)))
    
    for idx, row in sample_studies.iterrows():
        # study_path = settings.MURA_DATA_DIR / row['path']
        study_path = "data" / Path(row['path'])
        label = "POSITIVE" if row['label'] == 1 else "NEGATIVE"
        
        if study_path.exists():
            images = list(study_path.glob("*.png")) + list(study_path.glob("*.PNG"))
            print(f"   ✓ {row['path']} ({label}) - {len(images)} images")
        else:
            print(f"   ❌ {row['path']} non trouvé!")
    
    # 5. Aperçu des body parts
    print(f"\n4. Distribution par partie du corps:")
    body_parts = {}
    
    for path in train_df['path']:
        parts = Path(path).parts
        if len(parts) >= 2:
            # print(f"Path : {path}")
            body_part = parts[1]  # XR_ELBOW, XR_WRIST, etc.
            body_parts[body_part] = body_parts.get(body_part, 0) + 1
    
    for part, count in sorted(body_parts.items()):
        print(f"   - {part}: {count} études")
    
    print("\n" + "=" * 60)
    print("✅ Structure MURA valide!")
    print("=" * 60)
    
    return True


def create_sample_csv_if_missing():
    """Crée un CSV d'exemple si les fichiers n'existent pas"""
    
    if settings.MURA_TRAIN_CSV.exists() and settings.MURA_VAL_CSV.exists():
        return
    
    print("Création de CSVs d'exemple...")
    
    # Créer le dossier si nécessaire
    settings.MURA_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Exemple de contenu
    train_example = """MURA-v1.1/train/XR_WRIST/patient00001/study1_positive/,1
                        MURA-v1.1/train/XR_WRIST/patient00001/study2_negative/,0
                        MURA-v1.1/train/XR_ELBOW/patient00002/study1_positive/,1"""
    
    valid_example = """MURA-v1.1/valid/XR_WRIST/patient99999/study1_negative/,0"""
    
    with open(settings.MURA_TRAIN_CSV, 'w') as f:
        f.write(train_example)
    
    with open(settings.MURA_VAL_CSV, 'w') as f:
        f.write(valid_example)
    
    print(f"✓ CSVs créés dans {settings.MURA_DATA_DIR}")


if __name__ == '__main__':
    # Créer les CSVs s'ils n'existent pas
    create_sample_csv_if_missing()
    
    # Vérifier la structure
    verify_mura_structure()