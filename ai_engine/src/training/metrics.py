"""Métriques d'évaluation"""

import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score, confusion_matrix


def compute_metrics(predictions: np.ndarray, targets: np.ndarray, threshold: float = 0.5) -> dict:
    """Calcule les métriques de classification"""
    
    # Binariser les prédictions
    binary_preds = (predictions >= threshold).astype(int)
    binary_targets = targets.astype(int)
    
    # Métriques de base
    accuracy = accuracy_score(binary_targets, binary_preds)
    
    # AUC-ROC
    try:
        auc = roc_auc_score(binary_targets, predictions)
    except:
        auc = 0.5
    
    # Sensibilité et spécificité
    tn, fp, fn, tp = confusion_matrix(binary_targets, binary_preds, labels=[0, 1]).ravel()
    
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    
    return {
        'accuracy': accuracy,
        'auc': auc,
        'sensitivity': sensitivity,
        'specificity': specificity,
        'predictions': binary_preds.flatten()
    }