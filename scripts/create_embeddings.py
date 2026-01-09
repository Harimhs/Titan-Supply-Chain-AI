"""
Create embeddings for TITAN data - UPDATED FOR NEW SCHEMA
"""

import os
import json
import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

DATA_DIR = Path(__file__).parent.parent / "data"
CHROMA_PATH = DATA_DIR.parent / "chroma_db"


def main():
    print("🧠 Initializing Vector Database (ChromaDB)...")
    print(f"   Location: {CHROMA_PATH}")
    
    # Create directory if not exists
    CHROMA_PATH.mkdir(exist_ok=True)
    
    # Use local Sentence Transformer (free, fast)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    
    # --- 1. PRODUCT COLLECTION ---
    print("\n📦 Embedding Products...")
    collection_products = client.get_or_create_collection(
        name="titan_products",
        embedding_function=ef
    )
    
    products_path = DATA_DIR / "raw" / "products.csv"
    if products_path.exists():
        df_products = pd.read_csv(products_path)
        
        # NEW SCHEMA: sku, name, category, weight_kg, price_usd, manufacturer, lead_time_days
        docs = df_products.apply(
            lambda x: f"{x['name']} - Category: {x['category']} - Manufacturer: {x['manufacturer']} - Price: ${x['price_usd']}",
            axis=1
        ).tolist()
        
        ids = df_products['sku'].astype(str).tolist()
        
        metadatas = df_products[['sku', 'name', 'category', 'manufacturer', 'price_usd', 'lead_time_days']].to_dict('records')
        
        # Clear existing
        try:
            existing_ids = collection_products.get()['ids']
            if existing_ids:
                collection_products.delete(ids=existing_ids)
        except:
            pass
        
        # Add new
        collection_products.add(
            documents=docs,
            ids=ids,
            metadatas=metadatas
        )
        
        print(f"   ✅ Embedded {len(docs):,} products")
    else:
        print(f"   ⚠️  Products file not found: {products_path}")
    
    # --- 2. DISASTER COLLECTION ---
    print("\n🔥 Embedding Disaster Archives...")
    collection_disasters = client.get_or_create_collection(
        name="titan_disasters",
        embedding_function=ef
    )
    
    disasters_path = DATA_DIR / "raw" / "disasters.json"
    if disasters_path.exists():
        with open(disasters_path) as f:
            disasters = json.load(f)
        
        # NEW SCHEMA: id, name, type, location, severity, start_date, duration_days, affected_radius_km
        docs = [
            f"{d['name']} - Type: {d['type']} - Location: {d['location']} - Severity: {d['severity']} - Date: {d['start_date']} - Duration: {d['duration_days']} days - Affected radius: {d['affected_radius_km']}km"
            for d in disasters
        ]
        
        ids = [d['id'] for d in disasters]
        
        metadatas = [
            {
                'id': d['id'],
                'name': d['name'],
                'type': d['type'],
                'location': d['location'],
                'severity': str(d['severity']),
                'start_date': d['start_date'],
                'duration_days': d['duration_days'],
                'affected_radius_km': d['affected_radius_km']
            }
            for d in disasters
        ]
        
        # Clear existing
        try:
            existing_ids = collection_disasters.get()['ids']
            if existing_ids:
                collection_disasters.delete(ids=existing_ids)
        except:
            pass
        
        # Add new
        collection_disasters.add(
            documents=docs,
            ids=ids,
            metadatas=metadatas
        )
        
        print(f"   ✅ Embedded {len(docs)} disasters")
    else:
        print(f"   ⚠️  Disasters file not found: {disasters_path}")
    
    print(f"\n✅ Vector Database Ready!")
    print(f"   Location: {CHROMA_PATH}")
    print(f"   Collections: titan_products ({len(collection_products.get()['ids'])}), titan_disasters ({len(collection_disasters.get()['ids'])})")


if __name__ == "__main__":
    main()
