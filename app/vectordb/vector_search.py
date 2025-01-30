from typing import List
import numpy as np
import faiss
import sklearn


class VectorSearch:
    """
    A class to perform vector search using FAISS.
    """

    @staticmethod
    def run_faiss(vector, vectors, k=15):
        """
        Search for the most similar vectors using Faiss method.
        """
        index = faiss.IndexFlatL2(vectors.shape[1])
        index.add(vectors)
        _, indices = index.search(np.array([vector]), k)
        return indices[0]


    @staticmethod
    def run_sk(vector, vectors, k=15):
        """
        Search for the most similar vectors using scikit-learn method.
        """
        similarities = sklearn.metrics.pairwise_distances(
            [vector], vectors, metric="euclidean", n_jobs=-1
        )
        partition_indices = np.argpartition(similarities[0], k)
        indices = partition_indices[:k]
        return indices


    @staticmethod
    def search_vectors(
        query_embedding: List[float], embeddings: List[List[float]], top_n: int
    ) -> List[int]:
        """
        Searches for the most similar vectors to the query_embedding in the given embeddings.

        :param query_embedding: a list of floats representing the query vector.
        :param embeddings: a list of vectors to be searched, where each vector is a list of floats.
        :param top_n: the number of most similar vectors to return.
        :return: a list of indices of the top_n most similar vectors in the embeddings.
        """
        if isinstance(embeddings, list):
            embeddings = np.array(embeddings).astype(np.float32)
            
        call_search = VectorSearch.run_faiss
        indices = call_search(query_embedding, embeddings, top_n)
        
        return indices
