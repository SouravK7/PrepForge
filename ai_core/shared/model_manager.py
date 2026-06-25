"""
Singleton model manager.

Prevents duplicate model loading. All AI pipelines request models
through this manager, which caches loaded models in memory.
"""

from __future__ import annotations

from typing import Any, Optional

import spacy
from sentence_transformers import SentenceTransformer

from ai_core.shared.config_loader import config


class ModelManager:
    """
    Singleton model manager.

    Ensures each model is loaded exactly once into memory.
    All AI pipelines request models through this manager.
    Dramatically reduces memory usage and initialization time.
    """

    _instance: Optional[ModelManager] = None
    _models: dict[str, Any] = {}

    def __new__(cls) -> ModelManager:
        """Singleton pattern: only one ModelManager instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_embedding_model(self) -> SentenceTransformer:
        """
        Get or load the sentence embedding model.

        Loads once on first call, returns cached instance on subsequent calls.

        Returns:
            Loaded SentenceTransformer model.

        Raises:
            RuntimeError: If model loading fails.
        """
        model_key = "embedding_model"

        if model_key not in self._models:
            try:
                model_name = config.get_str(
                    "models",
                    "embedding.model_name",
                    "all-MiniLM-L6-v2",
                )
                print(f"Loading embedding model: {model_name}")
                self._models[model_key] = SentenceTransformer(model_name)
                print("[OK] Embedding model loaded")
            except Exception as e:
                raise RuntimeError(
                    f"Failed to load embedding model: {e}"
                ) from e

        return self._models[model_key]

    def get_spacy_model(self) -> spacy.Language:
        """
        Get or load the spaCy NLP model.

        Loads once on first call, returns cached instance on subsequent calls.

        Returns:
            Loaded spaCy language model.

        Raises:
            RuntimeError: If model loading fails.
        """
        model_key = "spacy_model"

        if model_key not in self._models:
            try:
                model_name = config.get_str(
                    "models",
                    "spacy.model_name",
                    "en_core_web_sm",
                )
                print(f"Loading spaCy model: {model_name}")
                self._models[model_key] = spacy.load(model_name)
                print("[OK] spaCy model loaded")
            except Exception as e:
                raise RuntimeError(
                    f"Failed to load spaCy model: {e}"
                ) from e

        return self._models[model_key]

    def get_model(self, model_name: str) -> Any:
        """
        Generic model getter for flexibility.

        Args:
            model_name: "embedding" or "spacy" or other registered model name.

        Returns:
            The requested model instance.

        Raises:
            ValueError: If model_name is not recognized.
        """
        if model_name == "embedding":
            return self.get_embedding_model()
        elif model_name == "spacy":
            return self.get_spacy_model()
        else:
            raise ValueError(f"Unknown model: {model_name}")

    def unload_all(self) -> None:
        """
        Unload all cached models.

        Used for testing and memory cleanup. Subsequent calls
        to getters will reload models.
        """
        self._models = {}
        print("All models unloaded")

    def get_loaded_models(self) -> list[str]:
        """Get list of currently loaded model names."""
        return list(self._models.keys())


# Global singleton instance
model_manager = ModelManager()
