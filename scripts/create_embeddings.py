#!/usr/bin/env python3
"""
Create embeddings for all entities in Neo4j and store in ChromaDB
"""
import sys
from pathlib import Path
import pandas as pd
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configuration
CHROMA_DB_PATH = project_root / "chroma_db"
MODEL_NAME = "all-MiniLM-L6-v2"  # Fast and efficient
DATA_DIR = project_root / "data" / "processed"  # FIXED PATH

def main():
    """Generate embeddings for all entities"""
    print("\n🧠 Initializing Vector Database (ChromaDB)...")
    print(f"   Location: {CHROMA_DB_PATH}\n")
    
    # Initialize ChromaDB
    client = chromadb.PersistentClient(
        path=str(CHROMA_DB_PATH),
        settings=Settings(anonymized_telemetry=False)
    )
    
    # Load embedding model
    print("📥 Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)
    print(f"   Model: {MODEL_NAME}\n")
    
    # Create/get collections
    products_collection = client.get_or_create_collection(
        name="titan_products",
        metadata={"description": "Product catalog embeddings"}
    )
    
    disasters_collection = client.get_or_create_collection(
        name="titan_disasters",
        metadata={"description": "Disaster archive embeddings"}
    )
    
    factories_collection = client.get_or_create_collection(
        name="titan_factories",
        metadata={"description": "Factory information embeddings"}
    )
    
    # Embed Products
    print("📦 Embedding Products...")
    products_file = DATA_DIR / "products.csv"
    
    if products_file.exists():
        products_df = pd.read_csv(products_file)
        
        for _, row in products_df.iterrows():
            text = f"{row['name']}: {row['description']} (Category: {row['category']}, Price: ${row['avg_price']}, Weight: {row['weight_kg']}kg)"
            embedding = model.encode(text).tolist()
            
            products_collection.add(
                ids=[row['id']],
                embeddings=[embedding],
                documents=[text],
                metadatas=[{
                    "name": row['name'],
                    "category": row['category'],
                    "price": float(row['avg_price'])
                }]
            )
        
        print(f"   ✅ Embedded {len(products_df)} products\n")
    else:
        print(f"   ⚠️  Products file not found: {products_file}\n")
    
    # Embed Disasters
    print("🔥 Embedding Disasters...")
    disasters_file = DATA_DIR / "disasters.csv"
    
    if disasters_file.exists():
        disasters_df = pd.read_csv(disasters_file)
        
        for _, row in disasters_df.iterrows():
            text = f"{row['type']} disaster ({row['severity']}) in {row['city']}, {row['country']}. {row['description']} Affected {row['affected_count']} entities. Status: {row['status']}"
            embedding = model.encode(text).tolist()
            
            disasters_collection.add(
                ids=[row['id']],
                embeddings=[embedding],
                documents=[text],
                metadatas=[{
                    "type": row['type'],
                    "severity": row['severity'],
                    "city": row['city'],
                    "country": row['country'],
                    "status": row['status']
                }]
            )
        
        print(f"   ✅ Embedded {len(disasters_df)} disasters\n")
    else:
        print(f"   ⚠️  Disasters file not found: {disasters_file}\n")
    
    # Embed Factories (for semantic search)
    print("🏭 Embedding Factories...")
    factories_file = DATA_DIR / "factories.csv"
    
    if factories_file.exists():
        factories_df = pd.read_csv(factories_file)
        
        # Only embed a sample (100) for performance
        sample_df = factories_df.sample(n=min(100, len(factories_df)))
        
        for _, row in sample_df.iterrows():
            text = f"Factory {row['id']} in {row['city']}, {row['country']}. Produces {row['product_type']}. Capacity: {row['capacity']} units. Status: {row['operational_status']}"
            embedding = model.encode(text).tolist()
            
            factories_collection.add(
                ids=[row['id']],
                embeddings=[embedding],
                documents=[text],
                metadatas=[{
                    "city": row['city'],
                    "country": row['country'],
                    "product_type": row['product_type'],
                    "status": row['operational_status']
                }]
            )
        
        print(f"   ✅ Embedded {len(sample_df)} factories (sample)\n")
    else:
        print(f"   ⚠️  Factories file not found: {factories_file}\n")
    
    print("="*70)
    print("✅ EMBEDDINGS COMPLETE!")
    print("="*70)
    print(f"\n📊 Summary:")
    print(f"   Products: {products_collection.count()}")
    print(f"   Disasters: {disasters_collection.count()}")
    print(f"   Factories: {factories_collection.count()}")
    print(f"\n💾 Stored in: {CHROMA_DB_PATH}")
    print()

if __name__ == "__main__":
    main()
