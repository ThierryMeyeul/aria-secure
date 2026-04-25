# ai_engine/config/__init__.py
"""
Module de configuration pour ARIA Secure AI Engine.
"""

from .base_config import BaseConfig
from .mura_config import MURAConfig
from .nih_config import NIHConfig

# Configuration active (à changer selon le dataset)
ACTIVE_DATASET = "MURA"  # "MURA" ou "NIH"


def get_config(dataset: str = None, **kwargs):
    """
    Factory function pour obtenir la configuration appropriée.
    
    Args:
        dataset: "MURA" ou "NIH"
        **kwargs: Paramètres supplémentaires pour la configuration
    
    Returns:
        Configuration object (MURAConfig ou NIHConfig)
    """
    dataset = dataset or ACTIVE_DATASET
    
    configs = {
        "MURA": MURAConfig,
        "NIH": NIHConfig,
        "mura": MURAConfig,
        "nih": NIHConfig,
    }
    
    if dataset.upper() not in configs:
        raise ValueError(f"Dataset '{dataset}' non supporté. Choisir parmi: {list(configs.keys())}")
    
    return configs[dataset.upper()](**kwargs)


__all__ = ["BaseConfig", "MURAConfig", "NIHConfig", "get_config", "ACTIVE_DATASET"]