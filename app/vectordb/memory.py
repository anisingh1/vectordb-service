"""
This module provides the Memory class that represents a memory storage system
for text and associated metadata, with functionality for saving, searching, and
managing memory entries.
"""
# pylint: disable = line-too-long, trailing-whitespace, trailing-newlines, line-too-long, missing-module-docstring, import-error, too-few-public-methods, too-many-instance-attributes, too-many-locals

import os, json
from typing import List, Dict, Any, Union

from .embedding import BaseEmbedder, Embedder
from .vector_search import VectorSearch
from .storage import Storage
from utils import Prefs


class Memory:
    """
    Memory class represents a memory storage system for text and associated metadata.
    It provides functionality for saving, searching, and managing memory entries.
    """

    def __init__(
        self,
        embeddings: Union[BaseEmbedder, str]
    ):
        """
        Initializes the Memory class.
        :param embedding_model: a string containing the name of the pre-trained model to be used for embeddings (default: "sentence-transformers/all-MiniLM-L6-v2").
        """
        self.threshold = Prefs().getFloatPref('similarity_threshold')
        self.memory = []
        self.index_counter = 0

        if isinstance(embeddings, str):
            if os.path.exists(os.path.join(embeddings, "config.json")):
                self.embedder = Embedder(embeddings)
                model_config = os.path.join(embeddings, 'config.json')
                with open(model_config) as f:
                    conf = json.load(f)
                    self.embedding_dimension = conf['hidden_size']
                    self.model_name = conf['_name_or_path']
            else:
                raise TypeError("Embeddings must be an Embedder instance or valid model path")
        else:
            raise TypeError("Embeddings must be an Embedder instance or valid model path")

        self.vector_search = VectorSearch(self.embedding_dimension)


    def get_model_name(self):
        return self.model_name
    
    
    def add_from_file(
        self, 
        memory_file: str = None
    ):
        load = Storage(memory_file).load_from_disk()
        self.memory = [] if len(load) != 1 else load[0]["memory"]


    def add(
        self,
        text: str,
        metadata: Union[List, List[dict], dict, str, None] = None
    ):
        """
        Saves the given texts and metadata to memory.
        :param texts: a string or a list of strings containing the texts to be saved.
        :param metadata: a dictionary or a list of dictionaries containing the metadata associated with the texts.
        """
        embedding = self.embedder.embed_text(text)
        entry = {
            "text": text,
            "metadata": metadata
        }
        self.memory.append(entry)
        self.vector_search.add_index(embedding)
        self.index_counter += 1


    def search(self, query: str, top_n: int = 1, unique: bool = False) -> List[Dict[str, Any]]:
        """
        Searches for the most similar chunks to the given query in memory.
        :param query: a string containing the query text.
        :param top_n: the number of most similar chunks to return. (default: 5)
        :param unique: chunks are filtered out to unique texts (default: False)
        :return: a list of dictionaries containing the top_n most similar chunks and their associated metadata.
        """

        if isinstance(query, list):
            query_embedding = self.embedder.embed_text(query)
        else:
            query_embedding = self.embedder.embed_text([query])[0]

        indices = self.vector_search.search_vectors(query_embedding, top_n)
        if unique:
            unique_indices = []
            seen_text_indices = set()  # Change the variable name
            for i in indices:
                text_index = self.memory[i[0]][
                    "text_index"
                ]  # Use text_index instead of metadata_index
                if (
                    text_index not in seen_text_indices
                ):  # Use seen_text_indices instead of seen_meta_indices
                    unique_indices.append(i)
                    seen_text_indices.add(
                        text_index
                    )  # Use seen_text_indices instead of seen_meta_indices
            indices = unique_indices

        results = [
            {
                "text": self.memory[i[0]]["text"],
                "metadata": self.memory[i[0]]["metadata"],
                "distance": i[1],
            }
            for i in indices
        ]
        return results


    def clear(self):
        """
        Clears the memory.
        """
        self.memory = []
        self.index_counter = 0


    def save(
        self,
        memory_file: str
    ):
        """
        Saves the contents of the memory to file.
        """
        Storage(memory_file).save_to_disk([{"memory": self.memory}])
