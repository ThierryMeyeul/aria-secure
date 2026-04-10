"""Construction et chargement des modèles"""

import torch
import torch.nn as nn
from torchvision import models
from typing import Dict, Optional, Tuple
import onnx
import onnxruntime as ort
import numpy as np

from config.settings import settings


class ARIAEfficientNet(nn.Module):
    """
    Modèle EfficientNet pour ARIA Secure
    Supporte classification binaire (MURA) et multi-label (NIH)
    """
    
    def __init__(
        self,
        num_classes: int,
        model_name: str = 'efficientnet_v2_s',
        pretrained: bool = True,
        dropout_rate: float = 0.3
    ):
        super().__init__()
        
        self.num_classes = num_classes
        self.model_name = model_name
        
        # Charger le modèle pré-entraîné
        if model_name == 'efficientnet_v2_s':
            weights = models.EfficientNet_V2_S_Weights.IMAGENET1K_V1 if pretrained else None
            base_model = models.efficientnet_v2_s(weights=weights)
            
            # Remplacer le classifieur
            in_features = base_model.classifier[1].in_features
            base_model.classifier = nn.Sequential(
                nn.Dropout(p=dropout_rate, inplace=True),
                nn.Linear(in_features, num_classes)
            )
            self.model = base_model
        
        elif model_name == 'resnet50':
            weights = models.ResNet50_Weights.IMAGENET1K_V2 if pretrained else None
            base_model = models.resnet50(weights=weights)
            in_features = base_model.fc.in_features
            base_model.fc = nn.Sequential(
                nn.Dropout(p=dropout_rate),
                nn.Linear(in_features, num_classes)
            )
            self.model = base_model
        
        elif model_name == 'densenet121':
            weights = models.DenseNet121_Weights.IMAGENET1K_V1 if pretrained else None
            base_model = models.densenet121(weights=weights)
            in_features = base_model.classifier.in_features
            base_model.classifier = nn.Sequential(
                nn.Dropout(p=dropout_rate),
                nn.Linear(in_features, num_classes)
            )
            self.model = base_model
        
        else:
            raise ValueError(f"Modèle inconnu: {model_name}")
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass"""
        return self.model(x)
    
    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        """Extrait les features avant la classification (pour Grad-CAM)"""
        if self.model_name == 'efficientnet_v2_s':
            # Pour EfficientNet, on prend la sortie avant le classifieur
            features = self.model.features(x)
            features = self.model.avgpool(features)
            return features.flatten(1)
        else:
            raise NotImplementedError(f"Feature extraction pour {self.model_name}")
    
    def get_last_conv_layer(self):
        """Retourne la dernière couche convolutionnelle pour Grad-CAM"""
        if self.model_name == 'efficientnet_v2_s':
            return self.model.features[-1]
        elif self.model_name == 'resnet50':
            return self.model.layer4[-1]
        else:
            return None


def build_model(
    num_classes: int,
    device: str = 'cpu',
    model_path: Optional[str] = None
) -> nn.Module:
    """
    Construit et charge un modèle
    
    Args:
        num_classes: Nombre de classes
        device: 'cuda' ou 'cpu'
        model_path: Chemin vers un modèle sauvegardé (optionnel)
    
    Returns:
        Modèle PyTorch
    """
    model = ARIAEfficientNet(
        num_classes=num_classes,
        model_name=settings.MODEL_NAME,
        pretrained=model_path is None
    )
    
    if model_path and model_path.exists():
        checkpoint = torch.load(model_path, map_location=device)
        
        # Gérer différents formats de sauvegarde
        if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
            model.load_state_dict(checkpoint['model_state_dict'])
        else:
            model.load_state_dict(checkpoint)
        
        print(f"[Model] Chargé depuis {model_path}")
    
    model = model.to(device)
    
    return model


class ONNXPredictor:
    """
    Prédicteur ONNX pour l'inférence rapide
    """
    
    def __init__(self, model_path: str, device: str = 'cpu'):
        self.device = device
        
        # Options ONNX Runtime
        providers = ['CPUExecutionProvider']
        if device == 'cuda':
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        
        self.session = ort.InferenceSession(model_path, providers=providers)
        
        # Métadonnées
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
    
    def predict(self, image_tensor: np.ndarray) -> np.ndarray:
        """
        Prédiction sur un batch d'images
        
        Args:
            image_tensor: Shape (B, C, H, W) normalisé
        
        Returns:
            Logits du modèle
        """
        # Vérifier les dimensions
        if len(image_tensor.shape) == 3:
            image_tensor = image_tensor[np.newaxis, ...]
        
        # Inférence
        outputs = self.session.run(
            [self.output_name],
            {self.input_name: image_tensor.astype(np.float32)}
        )[0]
        
        return outputs
    
    def predict_with_sigmoid(self, image_tensor: np.ndarray) -> np.ndarray:
        """Prédiction avec sigmoid pour les probabilités"""
        logits = self.predict(image_tensor)
        return 1 / (1 + np.exp(-logits))  # sigmoid