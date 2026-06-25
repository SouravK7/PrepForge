"""
Text preprocessing utilities.

Handles tokenization, lemmatization, stopword removal,
and other NLP preprocessing common across evaluators.
"""

from __future__ import annotations

import string
from typing import Optional

import nltk
import spacy
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

from ai_core.shared.model_manager import model_manager


class TextProcessor:
    """
    Unified text preprocessing service.

    Provides tokenization, lemmatization, stopword removal,
    and other NLP preprocessing utilities.
    """

    _lemmatizer: Optional[WordNetLemmatizer] = None
    _stop_words: Optional[set] = None
    _spacy_model: Optional[spacy.Language] = None

    @classmethod
    def _init_nltk(cls) -> None:
        """Initialize NLTK resources."""
        if cls._lemmatizer is None:
            cls._lemmatizer = WordNetLemmatizer()
            try:
                nltk.data.find("tokenizers/punkt")
            except LookupError:
                nltk.download("punkt", quiet=True)

            try:
                nltk.data.find("tokenizers/punkt_tab")
            except LookupError:
                nltk.download("punkt_tab", quiet=True)

            try:
                nltk.data.find("corpora/stopwords")
            except LookupError:
                nltk.download("stopwords", quiet=True)

            try:
                nltk.data.find("corpora/wordnet")
            except LookupError:
                nltk.download("wordnet", quiet=True)

            cls._stop_words = set(stopwords.words("english"))

    @classmethod
    def _get_spacy_model(cls) -> spacy.Language:
        """Get or load spaCy model."""
        if cls._spacy_model is None:
            cls._spacy_model = model_manager.get_spacy_model()
        return cls._spacy_model

    @staticmethod
    def tokenize(text: str) -> list[str]:
        """
        Tokenize text into words.

        Args:
            text: Text to tokenize.

        Returns:
            List of tokens.
        """
        return word_tokenize(text.lower())

    @classmethod
    def lemmatize(cls, text: str) -> list[str]:
        """
        Tokenize and lemmatize text.

        Args:
            text: Text to lemmatize.

        Returns:
            List of lemmatized tokens.
        """
        cls._init_nltk()
        tokens = cls.tokenize(text)
        return [cls._lemmatizer.lemmatize(token) for token in tokens]  # type: ignore[union-attr]

    @classmethod
    def remove_stopwords(cls, tokens: list[str]) -> list[str]:
        """
        Remove stopwords from token list.

        Args:
            tokens: Tokens to filter.

        Returns:
            Tokens without stopwords.
        """
        cls._init_nltk()
        return [t for t in tokens if t not in cls._stop_words]

    @classmethod
    def preprocess(cls, text: str, remove_stops: bool = True) -> list[str]:
        """
        Complete preprocessing: tokenize, lemmatize, optionally remove stopwords.

        Args:
            text: Text to preprocess.
            remove_stops: Whether to remove stopwords.

        Returns:
            Preprocessed tokens.
        """
        tokens = cls.lemmatize(text)
        if remove_stops:
            tokens = cls.remove_stopwords(tokens)
        return [t for t in tokens if t not in string.punctuation]

    @staticmethod
    def extract_pos_tags(text: str) -> list[tuple[str, str]]:
        """
        Extract part-of-speech tags using spaCy.

        Args:
            text: Text to analyze.

        Returns:
            List of (token, pos_tag) tuples.
        """
        nlp = model_manager.get_spacy_model()
        doc = nlp(text)
        return [(token.text, token.pos_) for token in doc]

    @staticmethod
    def extract_entities(text: str) -> list[dict[str, str]]:
        """
        Extract named entities using spaCy.

        Args:
            text: Text to analyze.

        Returns:
            List of entities with text and label.
        """
        nlp = model_manager.get_spacy_model()
        doc = nlp(text)
        return [
            {"text": ent.text, "label": ent.label_}
            for ent in doc.ents
        ]

    @staticmethod
    def sentence_count(text: str) -> int:
        """
        Count sentences in text using spaCy.

        Args:
            text: Text to analyze.

        Returns:
            Number of sentences.
        """
        nlp = model_manager.get_spacy_model()
        doc = nlp(text)
        return len(list(doc.sents))

    @staticmethod
    def word_count(text: str) -> int:
        """
        Count words in text.

        Args:
            text: Text to analyze.

        Returns:
            Number of words.
        """
        return len(text.split())
