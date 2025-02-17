"""
This module provides the Memory class that represents a memory storage system
for text and associated metadata, with functionality for saving, searching, and
managing memory entries.
"""
# pylint: disable = line-too-long, trailing-whitespace, trailing-newlines, line-too-long, missing-module-docstring, import-error, too-few-public-methods, too-many-instance-attributes, too-many-locals

import os, json
import pickle
from typing import List, Dict, Any, Union

from .embedder import Embedder
from .indexer import VectorIndex
from utils import Logger


class DB():
    def __init__(self, size: int, embedding_dimension: int):
        try:
            self.memory = []
            self.vector_index = VectorIndex(embedding_dimension)
            self.size = size
        except Exception as e:
            raise Exception(e)


logger = Logger()
class Memory:
    """
    Memory class represents a memory storage system for text and associated metadata.
    It provides functionality for saving, searching, and managing memory entries.
    """
    
    def __init__(self, model_path: str):
        self.db: Dict[str, DB] = {}
        if os.path.exists(os.path.join(model_path, "config.json")):
            self.embedder = Embedder(model_path)
            model_config = os.path.join(model_path, 'config.json')
            with open(model_config) as f:
                conf = json.load(f)
                self.embedding_dimension = conf['hidden_size']
                self.model_name = conf['_name_or_path']
        else:
            raise TypeError("Model not found.")
        

    def list_db(self) -> List[dict]:
        """
        Returns a list of all the databases in memory.
        """
        dbs = []
        for i in self.db:
            db_info = {}
            db_info["name"] = i
            db_info["size"] = self.db[i].size
            db_info["record_count"] = len(self.db[i].memory)
            dbs.append(db_info)
        return dbs
    
        
    def create_db(
        self,
        db_name: str,
        size: int
    ) -> None:   
        dbObj = DB(size, self.embedding_dimension)
        self.db[db_name] = dbObj
        
    
    def clean_db(
        self, 
        db_name: str,
        q=20
    ) -> None:
        """
        Clears the memory of earlier added entries
        """
        if q == 100:
            del self.db[db_name]
        elif q > 0 and q < 100:
            new_start_index = int((self.index_counter * q) / 100)
            index_to_remove = list(range(0, new_start_index-1, 1))
            self.db[db_name].vector_index.remove_index(index_to_remove)
            self.db[db_name].memory = self.db[db_name].memory[new_start_index:]


    def save_db(
        self,
        db_name: str
    ) -> bytes:
        """
        Saves the contents of the memory to file.
        """
        if db_name in self.db:        
            data = pickle.dumps(
                {
                    'db': db_name, 
                    'size': self.db[db_name].size, 
                    'memory': self.db[db_name].memory
                }
            )
            return data
        else:
            raise Exception("Database not found.")
        
        
    def restore_db(
        self, 
        memory_file: bytes
    ) -> None:
        try:
            load = pickle.loads(memory_file)
            db_name = load['db']
            size = load['size']
            record_count = len(load['memory'])

            self.db[db_name] = DB(size, self.embedding_dimension)
            self.db[db_name].memory = load['memory']
            for i in range(record_count):
                self.db[db_name].vector_index.add_index(self.embedder.embed_text(self.db[db_name].memory[i]["text"]))
        except Exception as e:
            raise Exception(f"Failed to load memory file: {e}")
        
        
    def get_model_name(self) -> str:
        return self.model_name


    def add(
        self,
        db_name: str,
        text: str,
        metadata: Union[List, List[dict], dict, str, None] = None
    ) -> None:
        """
        Saves the given texts and metadata to memory.
        :param texts: a string or a list of strings containing the texts to be saved.
        :param metadata: a dictionary or a list of dictionaries containing the metadata associated with the texts.
        """
        try:
            if db_name not in self.db:
                raise Exception("Database not found.")
            
            if len(self.db[db_name].memory) >= self.db[db_name].size:
                self.clean(q=20)
                
            embedding = self.embedder.embed_text(text)
            entry = {
                "text": text,
                "metadata": metadata
            }
            self.db[db_name].memory.append(entry)
            self.db[db_name].vector_index.add_index(embedding)
        except Exception as e:
            raise Exception(e)


    def search(
        self, 
        db_name: str,
        query: str, 
        top_n: int = 1, 
        unique: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Searches for the most similar chunks to the given query in memory.
        :param query: a string containing the query text.
        :param top_n: the number of most similar chunks to return. (default: 5)
        :param unique: chunks are filtered out to unique texts (default: False)
        :return: a list of dictionaries containing the top_n most similar chunks and their associated metadata.
        """
        if db_name not in self.db:
            raise Exception("Database not found.")

        if isinstance(query, list):
            query_embedding = self.embedder.embed_text(query)
        else:
            query_embedding = self.embedder.embed_text([query])[0]

        indices = self.db[db_name].vector_index.search_index(query_embedding, top_n)
        if unique:
            unique_indices = []
            seen_text_indices = set()  # Change the variable name
            for i in indices:
                text_index = self.db[db_name].memory[i[0]][
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
            results.append({
                "text": self.db[db_name].memory[i[0]]["text"],
                "metadata": self.db[db_name].memory[i[0]]["metadata"],
                "distance": i[1]
            })
        return results
