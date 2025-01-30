"""
This module provides the VectorSearch class for performing vector search using various algorithms.
"""

# pylint: disable = line-too-long, trailing-whitespace, trailing-newlines, line-too-long, missing-module-docstring, import-error, too-few-public-methods, too-many-instance-attributes, too-many-locals

from typing import List, Tuple
import numpy as np
import faiss


class VectorSearch:
    """
    A class to perform vector search using different methods (MRPT, Faiss, or scikit-learn).
    """
    
    def __init__(self, dim):
        self.index = faiss.IndexFlatIP(dim)


    def add_index(
        self, 
        query_vector: List[float]
    ) -> None:
        
        if isinstance(query_vector, list):
            query_vector = np.array(query_vector).astype(np.float32)
        
        query_vector = np.array([query_vector])
        faiss.normalize_L2(query_vector)
        self.index.add(query_vector)
        return
    

    def run_faiss(self, query_vector, top_n):
        """
        Search for the most similar vectors using Faiss method.
        """
        try:
            if top_n > self.index.ntotal:
                top_n = self.index.ntotal
                
            query_vector = np.array([query_vector])
            faiss.normalize_L2(query_vector)
            dis, indices = self.index.search(query_vector, top_n)
            return indices[0], dis[0]
        except Exception as e:
            print("Error in Faiss search: ", e)
            return [], []

    
    def search_vectors(
        self,
        query_embedding: List[float],
        top_n: int
    ) -> List[Tuple[int, float]]:
        """
        Searches for the most similar vectors to the query_embedding in the given embeddings.

        :param query_embedding: a list of floats representing the query vector.
        :param top_n: the number of most similar vectors to return.
        :return: a list of indices of the top_n most similar vectors in the embeddings.
        
        """
        if isinstance(query_embedding, list):
            query_embedding = np.array(query_embedding).astype(np.float32)

        indices, dis = self.run_faiss(query_embedding, top_n)
        return list(zip(indices, dis))