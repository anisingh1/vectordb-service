"""
This module provides classes for generating text embeddings using various pre-trained models.
"""

# pylint: disable = line-too-long, trailing-whitespace, trailing-newlines, line-too-long, missing-module-docstring, import-error, too-few-public-methods, too-many-instance-attributes, too-many-locals

from abc import ABC, abstractmethod
from typing import List
from sentence_transformers import SentenceTransformer


class BaseEmbedder(ABC):
    """Base class for Embedder."""

    @abstractmethod
    def embed_text(self, chunks: List[str]) -> List[List[float]]:
        """Generates embeddings for a list of text chunks."""


class Embedder(BaseEmbedder):
    """
    This class provides a way to generate embeddings for given text chunks using a specified
    pre-trained model.
    """

    def __init__(self, model_name: str):
        """
        Initializes the Embedder with a specified model.

        :param model_name: a string containing the name of the pre-trained model to be used
        for embeddings.
        """
        self.sbert = True
        if model_name == None or model_name == "":
            model_name = "model/paraphrase-multilingual-MiniLM-L12-v2"

        self.model = SentenceTransformer(model_name)
        print("OK.")


    def embed_text(self, chunks: List[str]) -> List[List[float]]:
        """
        Converts a list of text chunks into their corresponding embeddings.

        :param chunks: a list of strings containing the text chunks to be embedded.
        :return: a list of embeddings, where each embedding is represented as a list of floats.
        """
        if self.sbert:
            embeddings = self.model.encode(chunks).tolist()
        else:
            embeddings = self.model(chunks).numpy().tolist()
        return embeddings