#!/usr/bin/env python3
"""
Vector-based RAG using ChromaDB
Updated for new data structure
"""
import chromadb
from chromadb.config import Settings
from pathlib import Path

class VectorRAG:
    """Vector search using ChromaDB"""
    
    def __init__(self, chroma_path="chroma_db"):
        """Initialize ChromaDB connection"""
        self.chroma_path = Path(chroma_path)
        self.client = chromadb.PersistentClient(
            path=str(self.chroma_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Load collections
        self.products_collection = self.client.get_collection("titan_products")
        self.disasters_collection = self.client.get_collection("titan_disasters")
        self.factories_collection = self.client.get_collection("titan_factories")
        
        print("✅ Vector RAG initialized")
    
    def search_products(self, query, n_results=10):
        """Search for relevant products"""
        results = self.products_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        return {
            "type": "products",
            "query": query,
            "results": [
                {
                    "id": results['ids'][0][i],
                    "text": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i]
                }
                for i in range(len(results['ids'][0]))
            ]
        }
    
    def search_disasters(self, query, n_results=20):
        """Search for relevant disasters"""
        results = self.disasters_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        return {
            "type": "disasters",
            "query": query,
            "results": [
                {
                    "id": results['ids'][0][i],
                    "text": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i]
                }
                for i in range(len(results['ids'][0]))
            ]
        }
    
    def search_factories(self, query, n_results=30):
        """Search for relevant factories"""
        results = self.factories_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        return {
            "type": "factories",
            "query": query,
            "results": [
                {
                    "id": results['ids'][0][i],
                    "text": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i]
                }
                for i in range(len(results['ids'][0]))
            ]
        }
    
    def search_all(self, query, n_results=20):
        """Search across all collections"""
        products = self.search_products(query, n_results)
        disasters = self.search_disasters(query, n_results)
        factories = self.search_factories(query, n_results)
        
        return {
            "query": query,
            "products": products['results'],
            "disasters": disasters['results'],
            "factories": factories['results']
        }
