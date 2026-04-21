# ai_engine/config/nih_config.py
"""
Configuration spécifique pour le dataset NIH ChestX-ray14.
Classification multi-label de 14 pathologies pulmonaires.
"""

from dataclasses import dataclass, field
from typing import List, Dict
from .base_config import BaseConfig


@dataclass
class NIHConfig(BaseConfig):
    """Configuration pour l'entraînement sur NIH ChestX-ray14."""
    
    # Override des paramètres de base
    experiment_name: str = "nih_chest_pathologies"
    
    # Les 14 pathologies du dataset NIH
    pathologies: List[str] = field(default_factory=lambda: [
        "Atelectasis",
        "Cardiomegaly", 
        "Effusion",
        "Infiltration",
        "Mass",
        "Nodule",
        "Pneumonia",
        "Pneumothorax",
        "Consolidation",
        "Edema",
        "Emphysema",
        "Fibrosis",
        "Pleural_Thickening",
        "Hernia"
    ])
    
    num_classes: int = 14  # Multi-label classification
    
    # Paramètres spécifiques NIH
    batch_size: int = 32
    epochs: int = 40
    learning_rate: float = 1e-4
    
    # Gestion du déséquilibre des classes
    use_class_weights: bool = True
    class_weights: List[float] = None  # Calculé automatiquement
    
    # Métriques spécifiques pour multi-label
    primary_metric: str = "mean_auc"
    secondary_metrics: List[str] = field(default_factory=lambda: [
        "accuracy", "f1_macro", "f1_micro", "precision", "recall"
    ])
    
    # Seuils par pathologie
    thresholds: Dict[str, float] = field(default_factory=dict)
    
    # Paramètres de loss
    loss_function: str = "BCEWithLogitsLoss"  # Binary Cross Entropy pour multi-label
    label_smoothing: float = 0.1  # Pour éviter l'overconfidence
    
    def __post_init__(self):
        """Initialisation spécifique NIH."""
        super().__post_init__()
        
        # Chemins spécifiques NIH
        self.train_list = self.data_dir / "NIH" / "train_list.txt"
        self.valid_list = self.data_dir / "NIH" / "valid_list.txt"
        self.test_list = self.data_dir / "NIH" / "test_list.txt"
        self.labels_csv = self.data_dir / "NIH" / "Data_Entry_2017.csv"
        
        # Initialiser les seuils par défaut
        if not self.thresholds:
            self.thresholds = {p: 0.5 for p in self.pathologies}