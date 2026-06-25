"""
Tests for shared AI infrastructure.

Tests model loading, embedding generation, caching,
text processing, and similarity calculations.
"""

import numpy as np
import pytest

from ai_core.shared import (
    AILogger,
    ConfigLoader,
    EmbeddingService,
    ModelManager,
    SimilarityCalculator,
    TextProcessor,
    ai_logger,
    config,
    embedding_cache,
    model_manager,
)


class TestConfigLoader:
    """Tests for ConfigLoader."""

    def test_config_singleton(self) -> None:
        """ConfigLoader is a singleton."""
        config1 = ConfigLoader()
        config2 = ConfigLoader()
        assert config1 is config2

    def test_config_load_app_config(self) -> None:
        """app_config.yaml loads successfully."""
        app_name = config.get_str("app_config", "app.name")
        assert app_name == "AI Interview Assistant"

    def test_config_get_with_default(self) -> None:
        """get() returns default for missing keys."""
        value = config.get("nonexistent_config", "key", default="default_value")
        assert value == "default_value"

    def test_config_get_int(self) -> None:
        """get_int() returns integer values."""
        value = config.get_int(
            "app_config", "interview.default_questions_per_session", 10
        )
        assert isinstance(value, int)

    def test_config_get_float(self) -> None:
        """get_float() returns float values."""
        value = config.get_float("scoring_weights", "technical.concept", 0.0)
        assert isinstance(value, float)

    def test_config_get_bool(self) -> None:
        """get_bool() returns boolean values."""
        value = config.get_bool("app_config", "app.debug", False)
        assert isinstance(value, bool)

    def test_config_get_list(self) -> None:
        """get_list() returns list values."""
        value = config.get_list("models", "nltk.required_packages", [])
        assert isinstance(value, list)


class TestModelManager:
    """Tests for ModelManager."""

    def test_model_manager_singleton(self) -> None:
        """ModelManager is a singleton."""
        mm1 = ModelManager()
        mm2 = ModelManager()
        assert mm1 is mm2

    def test_get_embedding_model(self) -> None:
        """get_embedding_model() loads and caches model."""
        model = model_manager.get_embedding_model()
        assert model is not None

        # Second call returns same instance
        model2 = model_manager.get_embedding_model()
        assert model is model2

    def test_get_spacy_model(self) -> None:
        """get_spacy_model() loads and caches model."""
        model = model_manager.get_spacy_model()
        assert model is not None

        # Second call returns same instance
        model2 = model_manager.get_spacy_model()
        assert model is model2

    def test_get_loaded_models(self) -> None:
        """get_loaded_models() returns list of loaded models."""
        model_manager.unload_all()
        models = model_manager.get_loaded_models()
        assert len(models) == 0

        model_manager.get_embedding_model()
        models = model_manager.get_loaded_models()
        assert "embedding_model" in models


class TestEmbeddingCache:
    """Tests for EmbeddingCache."""

    def test_cache_put_and_get(self) -> None:
        """Cache stores and retrieves embeddings."""
        embedding_cache.clear()
        text = "test text"
        emb = np.random.randn(384)

        embedding_cache.put(text, emb)
        cached = embedding_cache.get(text)

        assert cached is not None
        assert np.allclose(cached, emb)

    def test_cache_miss(self) -> None:
        """Cache returns None for uncached text."""
        embedding_cache.clear()
        cached = embedding_cache.get("not cached")
        assert cached is None

    def test_cache_contains(self) -> None:
        """Cache.contains() checks existence."""
        embedding_cache.clear()
        text = "test"
        emb = np.random.randn(384)

        embedding_cache.put(text, emb)
        assert embedding_cache.contains(text)
        assert not embedding_cache.contains("not cached")

    def test_cache_size(self) -> None:
        """Cache.size() returns count."""
        embedding_cache.clear()
        assert embedding_cache.size() == 0

        for i in range(5):
            embedding_cache.put(f"text_{i}", np.random.randn(384))

        assert embedding_cache.size() == 5


class TestEmbeddingService:
    """Tests for EmbeddingService."""

    def test_embed_text(self) -> None:
        """embed_text() generates embeddings."""
        embedding_cache.clear()
        text = "This is a test sentence."
        emb = EmbeddingService.embed_text(text)

        assert isinstance(emb, np.ndarray)
        assert len(emb) == 384  # all-MiniLM-L6-v2 output size

    def test_embed_text_caching(self) -> None:
        """embed_text() caches and reuses embeddings."""
        embedding_cache.clear()
        text = "Cache test sentence."

        emb1 = EmbeddingService.embed_text(text)
        emb2 = EmbeddingService.embed_text(text)

        assert np.allclose(emb1, emb2)
        assert embedding_cache.size() == 1

    def test_embed_batch(self) -> None:
        """embed_batch() embeds multiple texts."""
        embedding_cache.clear()
        texts = [
            "First sentence.",
            "Second sentence.",
            "Third sentence.",
        ]
        embeddings = EmbeddingService.embed_batch(texts)

        assert len(embeddings) == 3
        for emb in embeddings:
            assert isinstance(emb, np.ndarray)
            assert len(emb) == 384

    def test_cache_stats(self) -> None:
        """cache_stats() returns stats."""
        embedding_cache.clear()
        stats = EmbeddingService.cache_stats()

        assert "cached_embeddings" in stats
        assert "max_cache_size" in stats


class TestTextProcessor:
    """Tests for TextProcessor."""

    def test_tokenize(self) -> None:
        """tokenize() splits text into tokens."""
        text = "Hello, world! This is a test."
        tokens = TextProcessor.tokenize(text)

        assert isinstance(tokens, list)
        assert len(tokens) > 0
        assert "hello" in tokens

    def test_lemmatize(self) -> None:
        """lemmatize() returns lemmatized tokens."""
        text = "running runs ran"
        tokens = TextProcessor.lemmatize(text)

        assert isinstance(tokens, list)
        assert "run" in tokens

    def test_remove_stopwords(self) -> None:
        """remove_stopwords() filters common words."""
        tokens = ["the", "quick", "brown", "fox", "is", "running"]
        filtered = TextProcessor.remove_stopwords(tokens)

        assert "quick" in filtered
        assert "the" not in filtered

    def test_preprocess(self) -> None:
        """preprocess() does full cleaning."""
        text = "The quick brown fox jumps over the lazy dog."
        tokens = TextProcessor.preprocess(text, remove_stops=True)

        assert isinstance(tokens, list)
        assert len(tokens) > 0
        assert all(isinstance(t, str) for t in tokens)

    def test_word_count(self) -> None:
        """word_count() counts words."""
        text = "one two three four five"
        count = TextProcessor.word_count(text)
        assert count == 5

    def test_sentence_count(self) -> None:
        """sentence_count() counts sentences."""
        text = "First sentence. Second sentence. Third."
        count = TextProcessor.sentence_count(text)
        assert count == 3


class TestSimilarityCalculator:
    """Tests for SimilarityCalculator."""

    def test_cosine_similarity(self) -> None:
        """cosine_similarity() computes similarity."""
        embedding_cache.clear()
        text1 = "The quick brown fox"
        text2 = "The quick brown fox"

        similarity = SimilarityCalculator.cosine_similarity(text1, text2)

        assert isinstance(similarity, float)
        assert 0.0 <= similarity <= 1.0
        assert similarity > 0.9  # Same text should be very similar

    def test_cosine_similarity_different_texts(self) -> None:
        """cosine_similarity() gives low score for different texts."""
        embedding_cache.clear()
        text1 = "The quick brown fox"
        text2 = "Unrelated content about programming"

        similarity = SimilarityCalculator.cosine_similarity(text1, text2)

        assert similarity < 0.7

    def test_jaccard_similarity(self) -> None:
        """jaccard_similarity() computes overlap."""
        text1 = "the quick brown fox"
        text2 = "the quick brown dog"

        similarity = SimilarityCalculator.jaccard_similarity(text1, text2)

        assert isinstance(similarity, float)
        assert 0.0 <= similarity <= 1.0

    def test_token_overlap(self) -> None:
        """token_overlap() counts matching tokens."""
        text1 = "python javascript java"
        text2 = "python javascript golang"

        overlap, total, ratio = SimilarityCalculator.token_overlap(text1, text2)

        assert overlap == 2
        assert total == 3
        assert ratio > 0.5

    def test_concept_overlap(self) -> None:
        """concept_overlap() checks concept presence."""
        concepts = ["inheritance", "polymorphism", "abstraction"]
        text = "We discussed inheritance and polymorphism extensively."

        found, missing, coverage = SimilarityCalculator.concept_overlap(
            concepts, text
        )

        assert len(found) == 2
        assert len(missing) == 1
        assert "inheritance" in found
        assert "abstraction" in missing


class TestAILogger:
    """Tests for AILogger."""

    def test_logger_creation(self) -> None:
        """AILogger creates successfully."""
        logger = AILogger()
        assert logger is not None
        assert logger.log_file.exists()

    def test_log_decision(self) -> None:
        """log_decision() writes to log file."""
        logger = AILogger()
        logger.log_decision(
            decision_type="test_decision",
            context={"test": "context"},
            output={"test": "output"},
            reasoning="This is a test",
            confidence=1.0,
        )

        # File should have content
        with open(logger.log_file, "r") as f:
            content = f.read()
            assert "test_decision" in content
