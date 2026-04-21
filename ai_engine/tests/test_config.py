# ai_engine/tests/test_config.py
"""
Tests pour vérifier que les configurations sont correctes.
"""

import pytest
import tempfile
from pathlib import Path

# Ajouter le chemin du projet au PYTHONPATH
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import BaseConfig, MURAConfig, NIHConfig, get_config


class TestBaseConfig:
    """Tests pour la configuration de base."""
    
    def test_base_config_creation(self):
        """Test la création d'une configuration de base."""
        config = BaseConfig()
        
        assert config.project_name == "ARIA_Secure"
        assert config.batch_size == 32
        assert config.epochs == 50
        assert config.learning_rate == 1e-4
    
    def test_directory_creation(self):
        """Test que les dossiers sont créés automatiquement."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = BaseConfig(
                checkpoint_dir=Path(tmpdir) / "checkpoints",
                log_dir=Path(tmpdir) / "logs"
            )
            
            assert config.checkpoint_dir.exists()
            assert config.log_dir.exists()
    
    def test_to_dict(self):
        """Test la conversion en dictionnaire."""
        config = BaseConfig(batch_size=64, epochs=100)
        config_dict = config.to_dict()
        
        assert config_dict["batch_size"] == 64
        assert config_dict["epochs"] == 100
        assert isinstance(config_dict["checkpoint_dir"], str)
    
    def test_from_dict(self):
        """Test la création depuis un dictionnaire."""
        config_dict = {
            "batch_size": 128,
            "epochs": 200,
            "learning_rate": 0.001
        }
        
        config = BaseConfig.from_dict(config_dict)
        
        assert config.batch_size == 128
        assert config.epochs == 200
        assert config.learning_rate == 0.001


class TestMURAConfig:
    """Tests pour la configuration MURA."""
    
    def test_mura_config_defaults(self):
        """Test les valeurs par défaut de MURA."""
        config = MURAConfig()
        
        assert config.experiment_name == "mura_fracture_detection"
        assert config.num_classes == 2
        assert config.batch_size == 16
        assert config.primary_metric == "auroc"
        assert len(config.body_parts) == 7  # Toutes les parties du corps
    
    def test_mura_config_custom_body_parts(self):
        """Test la configuration avec des parties du corps spécifiques."""
        config = MURAConfig(body_parts=["XR_WRIST", "XR_SHOULDER"])
        
        assert len(config.body_parts) == 2
        assert "XR_WRIST" in config.body_parts
        assert "XR_SHOULDER" in config.body_parts
    
    def test_mura_class_weights(self):
        """Test les poids des classes pour MURA."""
        config = MURAConfig()
        
        assert len(config.class_weights) == 2
        assert config.class_weights[1] > config.class_weights[0]  # Abnormal a plus de poids


class TestNIHConfig:
    """Tests pour la configuration NIH."""
    
    def test_nih_config_defaults(self):
        """Test les valeurs par défaut de NIH."""
        config = NIHConfig()
        
        assert config.experiment_name == "nih_chest_pathologies"
        assert config.num_classes == 14
        assert len(config.pathologies) == 14
        assert config.primary_metric == "mean_auc"
    
    def test_nih_pathologies_list(self):
        """Test que toutes les pathologies sont présentes."""
        config = NIHConfig()
        
        expected_pathologies = [
            "Atelectasis", "Cardiomegaly", "Effusion", "Infiltration",
            "Mass", "Nodule", "Pneumonia", "Pneumothorax", "Consolidation",
            "Edema", "Emphysema", "Fibrosis", "Pleural_Thickening", "Hernia"
        ]
        
        assert config.pathologies == expected_pathologies
    
    def test_nih_thresholds(self):
        """Test les seuils de classification."""
        config = NIHConfig()
        
        assert len(config.thresholds) == 14
        assert all(threshold == 0.5 for threshold in config.thresholds.values())


class TestConfigFactory:
    """Tests pour la factory de configuration."""
    
    def test_get_config_mura(self):
        """Test l'obtention d'une configuration MURA."""
        config = get_config("MURA")
        assert isinstance(config, MURAConfig)
        assert config.experiment_name == "mura_fracture_detection"
    
    def test_get_config_nih(self):
        """Test l'obtention d'une configuration NIH."""
        config = get_config("NIH")
        assert isinstance(config, NIHConfig)
        assert config.experiment_name == "nih_chest_pathologies"
    
    def test_get_config_case_insensitive(self):
        """Test que la factory est insensible à la casse."""
        config1 = get_config("mura")
        config2 = get_config("MURA")
        
        assert isinstance(config1, MURAConfig)
        assert isinstance(config2, MURAConfig)
    
    def test_get_config_invalid(self):
        """Test qu'une erreur est levée pour un dataset invalide."""
        with pytest.raises(ValueError, match="Dataset 'INVALID' non supporté"):
            get_config("INVALID")
    
    def test_get_config_with_kwargs(self):
        """Test la création avec des paramètres supplémentaires."""
        config = get_config("MURA", batch_size=64, epochs=100)
        
        assert config.batch_size == 64
        assert config.epochs == 100
        assert isinstance(config, MURAConfig)


if __name__ == "__main__":
    # Exécuter les tests
    pytest.main([__file__, "-v", "-s"])