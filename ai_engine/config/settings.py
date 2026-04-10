"""Configuration loader from .env file"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, Tuple

# Charger .env depuis la racine
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)


class Settings:
    """Centralized configuration class"""
    
    # ========== Environnement ==========
    ENV: str = os.getenv('ENV', 'development')
    CURRENT_PROJECT: str = os.getenv('CURRENT_PROJECT', 'MURA')
    
    # ========== Chemins ==========
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / 'data'
    MODELS_DIR: Path = BASE_DIR / 'models'
    LOGS_DIR: Path = BASE_DIR / 'logs'
    
    # NIH (Thorax)
    NIH_DATA_DIR: Path = DATA_DIR / 'NIH' / 'images'
    NIH_LABELS_CSV: Path = DATA_DIR / 'NIH' / 'Data_Entry_2017.csv'
    NIH_MODEL_PATH: Path = MODELS_DIR / 'nih_best_model.pt'
    NIH_ONNX_PATH: Path = MODELS_DIR / 'nih_aria_model.onnx'
    
    # MURA (Bone fractures)
    MURA_DATA_DIR: Path = DATA_DIR / 'MURA-v1.1'
    MURA_TRAIN_CSV: Path = DATA_DIR / 'MURA-v1.1' / os.getenv('MURA_TRAIN_CSV', 'train_image_paths.csv')
    MURA_VAL_CSV: Path = DATA_DIR / 'MURA-v1.1' / os.getenv('MURA_VAL_CSV', 'valid_image_paths.csv')
    MURA_MODEL_PATH: Path = MODELS_DIR / 'mura_best_model.pt'
    MURA_ONNX_PATH: Path = MODELS_DIR / 'mura_aria_model.onnx'
    
    # ========== Hyperparamètres ==========
    IMAGE_SIZE: int = int(os.getenv('IMAGE_SIZE', 224))
    BATCH_SIZE: int = int(os.getenv('BATCH_SIZE', 32))
    NUM_EPOCHS: int = int(os.getenv('NUM_EPOCHS', 50))
    LEARNING_RATE: float = float(os.getenv('LEARNING_RATE', 0.0001))
    WEIGHT_DECAY: float = float(os.getenv('WEIGHT_DECAY', 0.0001))
    NUM_WORKERS: int = int(os.getenv('NUM_WORKERS', 4))
    
    # ========== Modèle ==========
    MODEL_NAME: str = os.getenv('MODEL_NAME', 'efficientnet_v2_s')
    THRESHOLD: float = float(os.getenv('THRESHOLD', 0.5))
    CRITICAL_THRESHOLD: float = float(os.getenv('CRITICAL_THRESHOLD', 0.75))
    
    # ========== Device ==========
    @property
    def DEVICE(self) -> str:
        device = os.getenv('DEVICE', 'auto')
        if device == 'auto':
            import torch
            return 'cuda' if torch.cuda.is_available() else 'cpu'
        return device
    
    # ========== MLflow ==========
    MLFLOW_TRACKING_URI: str = os.getenv('MLFLOW_TRACKING_URI', 'http://localhost:5000')
    MLFLOW_MURA_EXPERIMENT_NAME: str = os.getenv('MLFLOW_MURA_EXPERIMENT_NAME', 'ARIA_MURA_Bone_Anomaly')
    MLFLOW_NIH_EXPERIMENT_NAME: str = os.getenv('MLFLOW_NIH_EXPERIMENT_NAME', 'ARIA_NIH_Chest_X-Ray')
    
    # ========== Logs ==========
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: Optional[Path] = Path(os.getenv('LOG_FILE', 'logs/mura_training.log')) if os.getenv('LOG_FILE') else None
    
    # ========== Méthodes utilitaires ==========
    def get_model_path(self, project: Optional[str] = None) -> Path:
        """Retourne le chemin du modèle pour un projet donné"""
        p = project or self.CURRENT_PROJECT
        if p == 'NIH':
            return self.NIH_MODEL_PATH
        return self.MURA_MODEL_PATH
    
    def get_onnx_path(self, project: Optional[str] = None) -> Path:
        """Retourne le chemin ONNX pour un projet donné"""
        p = project or self.CURRENT_PROJECT
        if p == 'NIH':
            return self.NIH_ONNX_PATH
        return self.MURA_ONNX_PATH
    
    def get_data_params(self, project: Optional[str] = None) -> dict:
        """Retourne les paramètres de dataset pour un projet"""
        p = project or self.CURRENT_PROJECT
        if p == 'NIH':
            return {
                'data_dir': self.NIH_DATA_DIR,
                'labels_csv': self.NIH_LABELS_CSV,
                'num_classes': 14,  # 14 pathologies thoraciques
                'class_names': [
                    'Atelectasis', 'Cardiomegaly', 'Consolidation', 'Edema',
                    'Effusion', 'Emphysema', 'Fibrosis', 'Hernia', 'Infiltration',
                    'Mass', 'No Finding', 'Nodule', 'Pleural_Thickening', 'Pneumonia',
                    'Pneumothorax'
                ]
            }
        else:  # MURA
            return {
                'data_dir': self.MURA_DATA_DIR,
                'train_csv': self.MURA_TRAIN_CSV,
                'val_csv': self.MURA_VAL_CSV,
                'num_classes': 1,  # Binaire: normal vs anormal
                'class_names': ['Normal', 'Anormal']
            }
    
    def create_dirs(self):
        """Crée les répertoires nécessaires"""
        self.MODELS_DIR.mkdir(parents=True, exist_ok=True)
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)


# Instance globale
settings = Settings()

if __name__ == "__main__":
    print("Configuration actuelle:")
    for attr in dir(settings):
        if not attr.startswith("_") and not callable(getattr(settings, attr)):
            print(f"{attr}: {getattr(settings, attr)}")