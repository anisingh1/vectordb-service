from abc import ABC, abstractmethod
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer, SimilarityFunction


class BaseEmbedder(ABC):
    """Base class for Embedder."""
    @abstractmethod
    def embed_text(self, chunks: List[str]) -> List[List[float]]:
        ...


class Embedder(BaseEmbedder):
    """
    This class provides a way to generate embeddings for given text chunks using a specified
    pre-trained model.
    """

    def __init__(self, model_name: str = ''):
        """
        Initializes the Embedder with a specified model.

        :param model_name: a string containing the name of the pre-trained model to be used
        for embeddings.
        """
        self.sbert = True
        print("Initiliazing embeddings: ", model_name)
        if model_name == '':
            model_name = "model/paraphrase-multilingual-MiniLM-L12-v2"

        self.model = SentenceTransformer(model_name)
        self.model.similarity_fn_name = SimilarityFunction.COSINE
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
    
    
    def search_vectors(self, query_embedding: List[float], embeddings: List[List[float]], top_n: int) -> List[int]:
        """
        Searches for the most similar vectors to the query_embedding in the given embeddings.

        :param query_embedding: a list of floats representing the query vector.
        :param embeddings: a list of vectors to be searched, where each vector is a list of floats.
        :param top_n: the number of most similar vectors to return.
        :return: a list of indices of the top_n most similar vectors in the embeddings.
        """
        if isinstance(embeddings, list):
            embeddings = np.array(embeddings).astype(np.float32)

        indices = self.model.similarity(query_embedding, embeddings)
        return indices
