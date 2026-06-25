"""
Shared AI infrastructure layer.

All AI pipelines depend on these utilities:
- ModelManager: singleton model loader
- EmbeddingService: centralized embedding generation
- EmbeddingCache: embedding caching to avoid recomputation
- TextProcessor: NLP text preprocessing
- SimilarityCalculator: similarity measures
- ConfigLoader: YAML config management
- AILogger: structured decision logging
"""

from ai_core.shared.config_loader import ConfigLoader, config
from ai_core.shared.ai_logger import AILogger, ai_logger
from ai_core.shared.model_manager import ModelManager, model_manager
from ai_core.shared.embedding_cache import EmbeddingCache, embedding_cache
from ai_core.shared.embedding_service import EmbeddingService
from ai_core.shared.text_processor import TextProcessor
from ai_core.shared.similarity import SimilarityCalculator

__all__ = [
    # Config
    "ConfigLoader",
    "config",
    # Logging
    "AILogger",
    "ai_logger",
    # Models
    "ModelManager",
    "model_manager",
    # Embeddings
    "EmbeddingService",
    "EmbeddingCache",
    "embedding_cache",
    # Text
    "TextProcessor",
    # Similarity
    "SimilarityCalculator",
]
