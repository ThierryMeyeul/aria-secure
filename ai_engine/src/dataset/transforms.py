"""Transformations et augmentations pour les radiographies"""

import albumentations as A
from albumentations.pytorch import ToTensorV2
import numpy as np
from typing import Dict, Any
import cv2


def get_transforms(mode: str, image_size: int = 224) -> A.Compose:
    """
    Retourne les transformations pour l'entraînement ou la validation
    
    Args:
        mode: 'train', 'val', ou 'test'
        image_size: Taille de redimensionnement (carré)
    
    Returns:
        Compose d'albumentations
    """
    if mode == 'train':
        return A.Compose([
            # Redimensionnement
            A.LongestMaxSize(max_size=image_size),
            # A.PadIfNeeded(
            #     min_height=image_size,
            #     min_width=image_size,
            #     border_mode=0,
            #     value=0
            # ),
            A.PadIfNeeded(
                min_height=image_size,
                min_width=image_size,
                border_mode=cv2.BORDER_CONSTANT
            ),
            
            # Augmentations géométriques
            A.RandomResizedCrop(
                size=(image_size, image_size),
                scale=(0.8, 1.0),
                ratio=(0.9, 1.1),
                p=0.5
            ),
            A.HorizontalFlip(p=0.5),
            A.Rotate(limit=15, border_mode=0, p=0.3),
            
            # Augmentations d'intensité (importantes pour les radios)
            A.RandomBrightnessContrast(
                brightness_limit=0.2,
                contrast_limit=0.2,
                p=0.4
            ),
            A.GaussNoise(std_range=(0.1, 0.2), p=0.2),
            A.ISONoise(color_shift=(0.01, 0.05), p=0.2),
            
            # Normalisation (valeurs ImageNet standard)
            A.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            ),
            
            # Conversion en tensor PyTorch
            ToTensorV2()
        ])
    
    else:  # validation ou test
        return A.Compose([
            A.LongestMaxSize(max_size=image_size),
            A.PadIfNeeded(
                min_height=image_size,
                min_width=image_size,
                border_mode=0,
                value=0
            ),
            A.CenterCrop(height=image_size, width=image_size),
            A.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            ),
            ToTensorV2()
        ])


class MedicalAugmentations:
    """
    Augmentations spécifiques aux radiographies médicales
    """
    
    @staticmethod
    def add_simulated_noise(image: np.ndarray, intensity: float = 0.1) -> np.ndarray:
        """Ajoute un bruit simulant les variations de dose"""
        noise = np.random.normal(0, intensity * 255, image.shape)
        return np.clip(image + noise, 0, 255).astype(np.uint8)
    
    @staticmethod
    def simulate_motion_blur(image: np.ndarray, kernel_size: int = 5) -> np.ndarray:
        """Simule un flou de mouvement (patient qui bouge)"""
        kernel = np.zeros((kernel_size, kernel_size))
        kernel[int((kernel_size-1)/2), :] = np.ones(kernel_size)
        kernel = kernel / kernel_size
        
        from scipy import ndimage
        return ndimage.convolve(image, kernel, mode='constant', cval=0.0)
    
    @staticmethod
    def adjust_window_level(
        image: np.ndarray,
        window_center: int = 40,
        window_width: int = 400
    ) -> np.ndarray:
        """Ajuste le niveau de fenêtre (simule différents réglages DICOM)"""
        # Implémentation simplifiée
        min_val = window_center - window_width // 2
        max_val = window_center + window_width // 2
        image = np.clip(image, min_val, max_val)
        image = (image - min_val) / (max_val - min_val) * 255
        return image.astype(np.uint8)