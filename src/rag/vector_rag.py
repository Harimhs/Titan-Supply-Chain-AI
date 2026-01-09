"""
VectorRAG: Semantic search over products, inventory, and facility metadata
Uses ChromaDB with sentence-transformers embeddings
"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict
from pathlib import Path
from src.utils.config import Config
import json

class VectorRAG:
    def __init__(self):
        """Initialize ChromaDB and embedding model"""
        # Create ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=str(Config.CHROMA_DB_PATH),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Embedding model (384-dim, fast)
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Collections
        self.products_collection = self._get_or_create_collection("products")
        self.facilities_collection = self._get_or_create_collection("facilities")
        
        print("✅ VectorRAG Initialized")
    
    def _get_or_create_collection(self, name: str):
        """Get or create ChromaDB collection"""
        try:
            collection = self.chroma_client.get_collection(name)
            print(f"   📚 Loaded collection: {name}")
        except:
            collection = self.chroma_client.create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
            print(f"   ✨ Created collection: {name}")
        return collection
    
    def index_products(self, products_df):
        """
        Index products from DataFrame
        Called during initial setup
        """
        print(f"📦 Indexing {len(products_df)} products...")
        
        documents = []
        metadatas = []
        ids = []
        
        for idx, row in products_df.iterrows():
            # Create rich text representation
            doc = f"{row['name']} ({row['sku']}). Category: {row['category']}/{row['subcategory']}. Origin: {row['origin_country']}. HS Code: {row['hs_code']}. Weight: {row['weight_kg']}kg, Value: ${row['value_usd']}"
            
            documents.append(doc)
            metadatas.append({
                "sku": row['sku'],
                "name": row['name'],
                "category": row['category'],
                "origin": row['origin_country']
            })
            ids.append(row['sku'])
            
            if len(documents) >= 1000:  # Batch insert
                embeddings = self.embedder.encode(documents).tolist()
                self.products_collection.add(
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    ids=ids
                )
                documents, metadatas, ids = [], [], []
                print(f"   Indexed {idx}/{len(products_df)}", end='\r')
        
        # Insert remaining
        if documents:
            embeddings = self.embedder.encode(documents).tolist()
            self.products_collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
        
        print(f"\n✅ Indexed {len(products_df)} products")
    
    def index_facilities(self, facilities_data: List[Dict]):
        """
        Index warehouses, factories, ports
        """
        print(f"🏭 Indexing {len(facilities_data)} facilities...")
        
        documents = []
        metadatas = []
        ids = []
        
        for facility in facilities_data:
            # Create searchable text
            doc = f"{facility['type']}: {facility.get('name', facility['id'])}. Located in {facility['city']}, {facility['country']}. Tier: {facility.get('tier', 'N/A')}"
            
            documents.append(doc)
            metadatas.append({
                "id": facility['id'],
                "type": facility['type'],
                "city": facility['city'],
                "country": facility['country']
            })
            ids.append(facility['id'])
        
        embeddings = self.embedder.encode(documents).tolist()
        self.facilities_collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"✅ Indexed {len(facilities_data)} facilities")
    
    def search_products(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Semantic search for products
        
        Example queries:
        - "iPhone 15 Pro Max"
        - "Electronics from China"
        - "Heavy machinery parts"
        """
        query_embedding = self.embedder.encode([query])[0].tolist()
        
        results = self.products_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        return self._format_results(results)
    
    def search_facilities(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Semantic search for facilities
        
        Example queries:
        - "Warehouses in Mumbai"
        - "Manufacturing facilities in China"
        - "Ports near Rotterdam"
        """
        query_embedding = self.embedder.encode([query])[0].tolist()
        
        results = self.facilities_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        return self._format_results(results)
    
    def _format_results(self, raw_results) -> List[Dict]:
        """Convert ChromaDB results to clean format"""
        if not raw_results['ids'] or not raw_results['ids'][0]:
            return []
        
        formatted = []
        for i in range(len(raw_results['ids'][0])):
            formatted.append({
                'id': raw_results['ids'][0][i],
                'document': raw_results['documents'][0][i],
                'metadata': raw_results['metadatas'][0][i],
                'distance': raw_results['distances'][0][i]
            })
        
        return formatted
    
    def get_context_for_query(self, query: str, max_tokens: int = 2000) -> str:
        """
        Get formatted context string for LLM
        
        Args:
            query: User query
            max_tokens: Token budget from DCBA
        
        Returns:
            Formatted context string
        """
        # Search both collections
        product_results = self.search_products(query, top_k=5)
        facility_results = self.search_facilities(query, top_k=3)
        
        context = "### VectorRAG Context\n\n"
        
        if product_results:
            context += "**Relevant Products:**\n"
            for i, result in enumerate(product_results[:3], 1):
                context += f"{i}. {result['document']}\n"
            context += "\n"
        
        if facility_results:
            context += "**Relevant Facilities:**\n"
            for i, result in enumerate(facility_results[:3], 1):
                context += f"{i}. {result['document']}\n"
            context += "\n"
        
        # Truncate to token budget (rough estimate: 1 token ≈ 4 chars)
        max_chars = max_tokens * 4
        if len(context) > max_chars:
            context = context[:max_chars] + "...\n[Context truncated due to token budget]"
        
        return context


# Quick test
if __name__ == "__main__":
    import pandas as pd
    from pathlib import Path
    
    print("🧪 Testing VectorRAG...")
    
    vector_rag = VectorRAG()
    
    # Test 1: Index products
    data_dir = Path(__file__).parent.parent.parent / "data"
    products_df = pd.read_csv(data_dir / "raw" / "products.csv")
    
    # Only index if collection is empty
    count = vector_rag.products_collection.count()
    if count == 0:
        print("\n📦 Indexing products (first time only)...")
        vector_rag.index_products(products_df.head(1000))  # Test with 1K products
    else:
        print(f"\n✅ Products already indexed: {count} items")
    
    # Test 2: Search
    print("\n🔍 Test Search: 'iPhone smartphone'")
    results = vector_rag.search_products("iPhone smartphone", top_k=3)
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['document'][:100]}...")
    
    # Test 3: Get context
    print("\n📄 Test Context Generation:")
    context = vector_rag.get_context_for_query("Where can I find electronics?", max_tokens=500)
    print(context[:300] + "...")
    
    print("\n✅ VectorRAG Tests Complete!")
