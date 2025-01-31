"""
This module provides the Memory class that represents a memory storage system
for text and associated metadata, with functionality for saving, searching, and
managing memory entries.
"""
# pylint: disable = line-too-long, trailing-whitespace, trailing-newlines, line-too-long, missing-module-docstring, import-error, too-few-public-methods, too-many-instance-attributes, too-many-locals

import os, json
from typing import List, Dict, Any, Union

from .embedding import BaseEmbedder, Embedder
from .index import VectorIndex
from .storage import Storage


class Memory:
    """
    Memory class represents a memory storage system for text and associated metadata.
    It provides functionality for saving, searching, and managing memory entries.
    """

    def __init__(
        self,
        embeddings: Union[BaseEmbedder, str],
        size: int = 10000,
        threshold: float = 0.5
    ):
        """
        Initializes the Memory class.
        :param embedding_model: a string containing the name of the pre-trained model to be used for embeddings (default: "sentence-transformers/all-MiniLM-L6-v2").
        """
        self.threshold = threshold
        self.size = size
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
        self.vector_index = VectorIndex(self.embedding_dimension)


    def get_model_name(self):
        return self.model_name
    
    
    def add_from_file(
        self, 
        memory_file: str = None
    ):
        load = Storage(memory_file).load_from_disk()
        record_count = len(load)
        
        if record_count > self.size:
            record_count = self.size

        self.memory = load[:record_count]
        self.index_counter = record_count-1
        for i in range(record_count):
            self.vector_index.add_index(self.embedder.embed_text(self.memory[i]["text"]))


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
        if self.index_counter == self.size:
            self.clean(q=20)
            
        embedding = self.embedder.embed_text(text)
        entry = {
            "text": text,
            "metadata": metadata
        }
        self.memory.append(entry)
        self.vector_index.add_index(embedding)
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

        indices = self.vector_index.search_index(query_embedding, top_n)
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

        results = []
        for i in indices:
            if i[1] > self.threshold:
                results.append({
                    "text": self.memory[i[0]]["text"],
                    "metadata": self.memory[i[0]]["metadata"],
                    "distance": i[1]
                })
        return results


    def clean(self, q=20):
        """
        Clears the memory of earlier added entries
        """
        if q == 100:
            new_start_index = self.vector_index.index.ntotal
            index_to_remove = list(range(0, new_start_index-1, 1))
            self.vector_index.remove_index(index_to_remove)
            self.memory = []
            self.index_counter = 0
        elif q > 0 and q < 100:
            new_start_index = int((self.index_counter * q) / 100)
            index_to_remove = list(range(0, new_start_index-1, 1))
            self.vector_index.remove_index(index_to_remove)
            self.memory = self.memory[new_start_index:]
            self.index_counter = self.index_counter - new_start_index


    def save(
        self
    ):
        """
        Saves the contents of the memory to file.
        """
        Storage("memory.pkl").save_to_disk(self.memory)
