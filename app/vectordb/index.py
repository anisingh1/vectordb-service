"""
This module provides the VectorIndex class for performing vector search using various algorithms.
"""

# pylint: disable = line-too-long, trailing-whitespace, trailing-newlines, line-too-long, missing-module-docstring, import-error, too-few-public-methods, too-many-instance-attributes, too-many-locals

from typing import List, Tuple
import numpy as np
import faiss
from utils import Logger


logger = Logger()
class VectorIndex:
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
    
    
    def remove_index(
        self, 
        index: int | List[int]
    ) -> None:
        if isinstance(index, int):
            index = [index]
        
        ids_to_remove = np.array(index, dtype=np.int64)
        self.index.remove_ids(ids_to_remove)
        return

    
    def search_index(
        self,
        query_vector: List[float],
        top_n: int
    ) -> List[Tuple[int, float]]:
        """
        Searches for the most similar vectors to the query_vector in the given embeddings.
        :param query_vector: a list of floats representing the query vector.
        :param top_n: the number of most similar vectors to return.
        :return: a list of indices of the top_n most similar vectors in the embeddings.
        
        """
        if isinstance(query_vector, list):
            query_vector = np.array(query_vector).astype(np.float32)

        indices, dis = self.run_faiss(query_vector, top_n)
        try:
            if top_n > self.index.ntotal:
                top_n = self.index.ntotal
                
            query_vector = np.array([query_vector])
            faiss.normalize_L2(query_vector)
            dis, indices = self.index.search(query_vector, top_n)
        except Exception as e:
            raise Exception(f"Faiss search failed: {e}")
        
        return list(zip(indices[0], dis[0]))