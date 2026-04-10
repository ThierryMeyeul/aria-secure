"""Utilitaires MLflow"""

import mlflow


def setup_mlflow(tracking_uri: str = 'http://localhost:5000'):
    """Configure MLflow"""
    mlflow.set_tracking_uri(tracking_uri)
    
    # Désactiver le logging automatique pour éviter les conflits
    mlflow.pytorch.autolog(disable=True)