import os
import json
import pickle
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple, Optional, List
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

logger = logging.getLogger(__name__)

MODELS_DIR = "models"
MODEL_METADATA_SUFFIX = "_metadata.json"

class LocalModelTrainer:
    """Service for training local classifiers on user-corrected data"""

    def __init__(self):
        """Initialize trainer and create models directory"""
        os.makedirs(MODELS_DIR, exist_ok=True)
        logger.info(f"LocalModelTrainer initialized with models_dir: {MODELS_DIR}")

    def train_model(
        self,
        dataset_id: int,
        dataset_name: str,
        texts: List[str],
        labels: List[str],
        model_type: str = "logistic_regression"
    ) -> Dict:
        """
        Train a local classifier on reviewed data.

        Args:
            dataset_id: Dataset ID for model naming
            dataset_name: Dataset name for metadata
            texts: List of text inputs
            labels: List of corresponding labels
            model_type: Type of model ('logistic_regression' or 'random_forest')

        Returns:
            Dict with training metadata and metrics

        Raises:
            ValueError: If insufficient data or invalid inputs
        """
        if len(texts) < 2:
            raise ValueError(f"Need at least 2 samples, got {len(texts)}")

        if len(set(labels)) < 2:
            raise ValueError(f"Need at least 2 unique classes, got {len(set(labels))}")

        if len(texts) != len(labels):
            raise ValueError("Texts and labels must have same length")

        logger.info(
            f"Starting model training for dataset {dataset_id} ({dataset_name}): "
            f"{len(texts)} samples, {len(set(labels))} classes"
        )

        try:
            # Vectorize text data
            vectorizer = TfidfVectorizer(
                max_features=1000,
                min_df=1,
                max_df=0.9,
                ngram_range=(1, 2),
                lowercase=True,
                stop_words='english'
            )

            X = vectorizer.fit_transform(texts)
            y = np.array(labels)

            logger.info(f"Vectorization complete: {X.shape} feature matrix")

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y,
                test_size=0.2,
                random_state=42,
                stratify=y
            )

            # Train model
            if model_type == "random_forest":
                model = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=20,
                    random_state=42,
                    n_jobs=-1
                )
                logger.info("Training RandomForest model...")
            else:
                model = LogisticRegression(
                    max_iter=1000,
                    random_state=42,
                    n_jobs=-1
                )
                logger.info("Training LogisticRegression model...")

            model.fit(X_train, y_train)

            # Evaluate
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
            recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
            f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)

            logger.info(
                f"Model trained - Accuracy: {accuracy:.4f}, "
                f"Precision: {precision:.4f}, Recall: {recall:.4f}, F1: {f1:.4f}"
            )

            # Save model and vectorizer
            model_path = self._get_model_path(dataset_id)
            vectorizer_path = self._get_vectorizer_path(dataset_id)

            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            logger.info(f"Model saved to {model_path}")

            with open(vectorizer_path, 'wb') as f:
                pickle.dump(vectorizer, f)
            logger.info(f"Vectorizer saved to {vectorizer_path}")

            # Save metadata
            metadata = {
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "model_type": model_type,
                "training_date": datetime.utcnow().isoformat(),
                "training_samples": len(texts),
                "n_classes": len(set(labels)),
                "classes": sorted(list(set(labels))),
                "test_samples": len(y_test),
                "accuracy": float(accuracy),
                "precision": float(precision),
                "recall": float(recall),
                "f1_score": float(f1),
                "n_features": X.shape[1],
                "vectorizer_params": {
                    "max_features": 1000,
                    "min_df": 1,
                    "max_df": 0.9,
                    "ngram_range": [1, 2]
                }
            }

            metadata_path = self._get_metadata_path(dataset_id)
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Metadata saved to {metadata_path}")

            return metadata

        except Exception as e:
            logger.error(f"Model training failed: {str(e)}")
            raise

    def predict(self, dataset_id: int, text: str) -> Tuple[str, float]:
        """
        Use trained model for prediction.

        Args:
            dataset_id: Dataset ID to find model
            text: Text to classify

        Returns:
            Tuple of (predicted_label, confidence_score)

        Raises:
            ValueError: If model not found
        """
        model_path = self._get_model_path(dataset_id)
        vectorizer_path = self._get_vectorizer_path(dataset_id)

        if not os.path.exists(model_path) or not os.path.exists(vectorizer_path):
            raise ValueError(f"No trained model found for dataset {dataset_id}")

        try:
            with open(model_path, 'rb') as f:
                model = pickle.load(f)

            with open(vectorizer_path, 'rb') as f:
                vectorizer = pickle.load(f)

            # Vectorize input
            X = vectorizer.transform([text])

            # Predict
            label = model.predict(X)[0]

            # Get confidence
            if hasattr(model, 'predict_proba'):
                probabilities = model.predict_proba(X)[0]
                confidence = float(np.max(probabilities))
            else:
                confidence = 0.5  # Default for models without probability

            logger.debug(
                f"Model prediction for dataset {dataset_id}: "
                f"label={label}, confidence={confidence:.4f}"
            )

            return label, confidence

        except Exception as e:
            logger.error(f"Model prediction failed: {str(e)}")
            raise

    def model_exists(self, dataset_id: int) -> bool:
        """Check if trained model exists for dataset"""
        return os.path.exists(self._get_model_path(dataset_id))

    def get_metadata(self, dataset_id: int) -> Optional[Dict]:
        """Get model metadata if it exists"""
        metadata_path = self._get_metadata_path(dataset_id)

        if not os.path.exists(metadata_path):
            return None

        try:
            with open(metadata_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read metadata: {str(e)}")
            return None

    def delete_model(self, dataset_id: int) -> bool:
        """Delete trained model and artifacts"""
        try:
            paths = [
                self._get_model_path(dataset_id),
                self._get_vectorizer_path(dataset_id),
                self._get_metadata_path(dataset_id)
            ]

            for path in paths:
                if os.path.exists(path):
                    os.remove(path)
                    logger.info(f"Deleted {path}")

            return True
        except Exception as e:
            logger.error(f"Failed to delete model: {str(e)}")
            return False

    def list_models(self) -> List[Dict]:
        """List all trained models with metadata"""
        models = []

        if not os.path.exists(MODELS_DIR):
            return models

        for file in os.listdir(MODELS_DIR):
            if file.endswith(MODEL_METADATA_SUFFIX):
                try:
                    with open(os.path.join(MODELS_DIR, file), 'r') as f:
                        metadata = json.load(f)
                        models.append(metadata)
                except Exception as e:
                    logger.error(f"Failed to load metadata {file}: {str(e)}")

        return sorted(models, key=lambda x: x['training_date'], reverse=True)

    @staticmethod
    def _get_model_path(dataset_id: int) -> str:
        return os.path.join(MODELS_DIR, f"dataset_{dataset_id}_model.pkl")

    @staticmethod
    def _get_vectorizer_path(dataset_id: int) -> str:
        return os.path.join(MODELS_DIR, f"dataset_{dataset_id}_vectorizer.pkl")

    @staticmethod
    def _get_metadata_path(dataset_id: int) -> str:
        return os.path.join(MODELS_DIR, f"dataset_{dataset_id}{MODEL_METADATA_SUFFIX}")
