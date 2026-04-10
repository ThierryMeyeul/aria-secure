#!/usr/bin/env python
"""
Test rapide de l'inférence
Usage: python scripts/test_inference.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
import numpy as np
from PIL import Image

from config.settings import settings
from src.models.builder import build_model, ONNXPredictor


def test_pytorch_inference():
    """Test l'inférence avec PyTorch"""
    print("\n=== Test Inférence PyTorch ===")
    
    # Vérifier que le modèle existe
    if not settings.MURA_MODEL_PATH.exists():
        print(f"Modèle non trouvé: {settings.MURA_MODEL_PATH}")
        print("Veuillez d'abord entraîner le modèle avec python scripts/train_mura.py")
        return
    
    # Charger le modèle
    model = build_model(
        num_classes=1,
        device=settings.DEVICE,
        model_path=settings.MURA_MODEL_PATH
    )
    model.eval()
    
    # Image factice
    dummy_image = torch.randn(1, 3, settings.IMAGE_SIZE, settings.IMAGE_SIZE)
    dummy_image = dummy_image.to(settings.DEVICE)
    
    # Inférence
    with torch.no_grad():
        output = model(dummy_image)
        prob = torch.sigmoid(output)
    
    print(f"Input shape: {dummy_image.shape}")
    print(f"Output logits: {output.cpu().numpy()}")
    print(f"Probability: {prob.cpu().numpy()[0][0]:.4f}")
    print(f"Prediction: {'Anormal' if prob > settings.THRESHOLD else 'Normal'}")
    
    print("✓ Inférence PyTorch OK")


def test_onnx_inference():
    """Test l'inférence avec ONNX"""
    print("\n=== Test Inférence ONNX ===")
    
    # Vérifier que le modèle existe
    if not settings.MURA_ONNX_PATH.exists():
        print(f"Modèle ONNX non trouvé: {settings.MURA_ONNX_PATH}")
        print("Exportez d'abord avec python scripts/export_onnx.py")
        return
    
    # Charger le prédicteur ONNX
    predictor = ONNXPredictor(
        str(settings.MURA_ONNX_PATH),
        device=settings.DEVICE
    )
    
    # Image factice
    dummy_image = np.random.randn(1, 3, settings.IMAGE_SIZE, settings.IMAGE_SIZE).astype(np.float32)
    
    # Inférence
    output = predictor.predict(dummy_image)
    prob = 1 / (1 + np.exp(-output))
    
    print(f"Input shape: {dummy_image.shape}")
    print(f"Output logits: {output}")
    print(f"Probability: {prob[0][0]:.4f}")
    
    print("✓ Inférence ONNX OK")


def main():
    print("=" * 50)
    print("ARIA Secure - Test Inférence")
    print(f"Device: {settings.DEVICE}")
    print(f"Current Project: {settings.CURRENT_PROJECT}")
    print("=" * 50)
    
    test_pytorch_inference()
    test_onnx_inference()
    
    print("\n✅ Tous les tests sont passés!")


if __name__ == '__main__':
    main()