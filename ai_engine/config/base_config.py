# ai_engine/config/base_config.py
"""
Configuration de base pour tous les datasets.
Les configurations spécifiques héritent de cette classe.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from pathlib import Path


@dataclass
class BaseConfig:
    """Configuration de base pour l'entraînement."""
    
    # Informations du projet
    project_name: str = "ARIA_Secure"
    experiment_name: str = "base_experiment"
    version: str = "1.0.0"
    
    # Chemins
    data_dir: Path = field(default_factory=lambda: Path("./data"))
    checkpoint_dir: Path = field(default_factory=lambda: Path("./checkpoints"))
    log_dir: Path = field(default_factory=lambda: Path("./logs"))
    
    # Paramètres d'entraînement
    batch_size: int = 32
    num_workers: int = 4
    epochs: int = 50
    learning_rate: float = 1e-4
    weight_decay: float = 1e-4
    
    # Optimiseur
    optimizer: str = "AdamW"  # AdamW, SGD, Adam
    scheduler: str = "CosineAnnealingLR"  # CosineAnnealingLR, ReduceLROnPlateau
    
    # Early stopping
    early_stopping_patience: int = 10
    min_delta: float = 1e-4
    
    # Modèle
    model_name: str = "efficientnet_v2_s"
    pretrained: bool = True
    num_classes: int = 1  # À surcharger
    
    # Dimensions des images
    image_size: Tuple[int, int] = (224, 224)
    input_channels: int = 3
    
    # Data augmentation
    use_augmentation: bool = True
    augmentation_prob: float = 0.5
    
    # Logging
    log_interval: int = 10  # Log tous les N batches
    eval_interval: int = 1  # Évaluation tous les N epochs
    
    # Device
    device: str = "cuda"  # "cuda" ou "cpu"
    
    # Reproducibilité
    seed: int = 42
    
    def __post_init__(self):
        """Créer les dossiers nécessaires."""
        self.checkpoint_dir = Path(self.checkpoint_dir) / self.experiment_name
        self.log_dir = Path(self.log_dir) / self.experiment_name
        
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> dict:
        """Convertir la configuration en dictionnaire."""
        return {k: str(v) if isinstance(v, Path) else v 
                for k, v in self.__dict__.items()}
    
    @classmethod
    def from_dict(cls, config_dict: dict):
        """Créer une configuration depuis un dictionnaire."""
        return cls(**config_dict)