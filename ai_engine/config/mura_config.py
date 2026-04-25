# ai_engine/config/mura_config.py
"""
Configuration spécifique pour le dataset MURA.
MURA est un dataset de radiographies musculosquelettiques pour la détection de fractures.
Classification binaire : normal vs anormal.
"""

from dataclasses import dataclass, field
from typing import List, Tuple
from .base_config import BaseConfig


@dataclass
class MURAConfig(BaseConfig):
    """Configuration pour l'entraînement sur MURA."""
    
    # Override des paramètres de base
    experiment_name: str = "mura_fracture_detection"
    num_classes: int = 2  # Classification binaire : normal vs abnormal
    
    # Paramètres spécifiques MURA
    body_parts: List[str] = None  # None = toutes les parties
    
    # Parties du corps disponibles dans MURA
    available_body_parts: List[str] = field(default_factory=lambda: [
        "XR_ELBOW", "XR_FINGER", "XR_FOREARM", "XR_HAND", 
        "XR_HUMERUS", "XR_SHOULDER", "XR_WRIST"
    ])
    
    # Paramètres d'entraînement spécifiques
    batch_size: int = 16  # MURA a des images de haute résolution
    epochs: int = 30
    learning_rate: float = 5e-5  # Plus petit pour fine-tuning
    
    # Métriques spécifiques
    primary_metric: str = "auroc"  # Area Under ROC Curve
    secondary_metrics: List[str] = field(default_factory=lambda: [
        "accuracy", "sensitivity", "specificity", "f1_score"
    ])
    
    # Seuil de classification
    classification_threshold: float = 0.5
    
    def __post_init__(self):
        """Initialisation spécifique MURA."""
        super().__post_init__()
        
        # Si aucune partie du corps spécifiée, utiliser toutes
        if self.body_parts is None:
            self.body_parts = self.available_body_parts
        
        # Chemins spécifiques MURA
        self.train_csv = self.data_dir / "MURA-v1.1" / "train.csv"
        self.valid_csv = self.data_dir / "MURA-v1.1" / "valid.csv"
        
        # Poids des classes pour gérer le déséquilibre
        self.class_weights = [1.0, 1.5]  # Poids plus élevé pour la classe anormale