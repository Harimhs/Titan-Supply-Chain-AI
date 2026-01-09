"""
Master data generation script - Run this ONE file!
OPTIMIZED: 50% reduced counts for faster generation
"""

import os
import sys
import json
import pandas as pd

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.synthetic.generate_geography import generate_factories, generate_ports, generate_warehouses
from data.synthetic.generate_supply_chain import generate_routes, generate_inventory
from data.synthetic.generate_disruptions import generate_disasters

# Create directories
os.makedirs('data/raw', exist_ok=True)
os.makedirs('data/processed', exist_ok=True)

def main():
    print("\n" + "="*70)
    print("🌍 TITAN DATA GENERATION STARTING... (OPTIMIZED)")
    print("="*70 + "\n")
    
    # Step 1: Products (5 products)
    print("📦 STEP 1/8: Creating products...")
    products = pd.DataFrame([
        {'sku': 'PROD-00001', 'name': 'iPhone 15 Pro 256GB', 'category': 'Electronics', 
         'weight_kg': 0.25, 'price_usd': 1299, 'manufacturer': 'Apple', 'lead_time_days': 28},
        {'sku': 'PROD-00002', 'name': 'Toyota Camry 2024', 'category': 'Automotive',
         'weight_kg': 1520, 'price_usd': 28000, 'manufacturer': 'Toyota', 'lead_time_days': 45},
        {'sku': 'PROD-00003', 'name': 'Pfizer COVID Vaccine', 'category': 'Pharma',
         'weight_kg': 0.005, 'price_usd': 20, 'manufacturer': 'Pfizer', 'lead_time_days': 60},
        {'sku': 'PROD-00004', 'name': 'Zara Cotton T-Shirt', 'category': 'Textiles',
         'weight_kg': 0.15, 'price_usd': 29, 'manufacturer': 'Inditex', 'lead_time_days': 21},
        {'sku': 'PROD-00005', 'name': 'Lavazza Coffee 500g', 'category': 'FMCG',
         'weight_kg': 0.5, 'price_usd': 12, 'manufacturer': 'Lavazza', 'lead_time_days': 18}
    ])
    products.to_csv('data/raw/products.csv', index=False)
    print(f"✅ Generated {len(products)} products\n")
    
    # Step 2: Factories (25K - REDUCED)
    print("🏭 STEP 2/8: Generating factories (25,000)...")
    factories_gdf = generate_factories(count=25000)
    factories_gdf.to_file('data/raw/factories.geojson', driver='GeoJSON')
    print(f"✅ Generated {len(factories_gdf):,} factories\n")
    
    # Step 3: Ports (1K - REDUCED)
    print("⚓ STEP 3/8: Generating ports (1,000)...")
    ports_gdf = generate_ports(count=1000)
    ports_gdf.to_file('data/raw/ports.geojson', driver='GeoJSON')
    print(f"✅ Generated {len(ports_gdf):,} ports\n")
    
    # Step 4: Warehouses (250K - REDUCED)
    print("📦 STEP 4/8: Generating warehouses (250,000)...")
    print("   (This will take 2-3 minutes...)")
    warehouses_gdf = generate_warehouses(count=250000)
    warehouses_gdf.to_file('data/raw/warehouses.geojson', driver='GeoJSON')
    print(f"✅ Generated {len(warehouses_gdf):,} warehouses\n")
    
    # Step 5: Routes (750K - REDUCED)
    print("🛣️  STEP 5/8: Generating supply routes (750,000)...")
    print("   (This will take 3-5 minutes...)")
    routes_df = generate_routes(factories_gdf, ports_gdf, warehouses_gdf, target=750000)
    routes_df.to_parquet('data/processed/routes.parquet', index=False, compression='snappy')
    print(f"✅ Generated {len(routes_df):,} routes\n")
    
    # Step 6: Inventory (500K - REDUCED)
    print("📊 STEP 6/8: Generating inventory snapshot (500,000)...")
    inventory_df = generate_inventory(warehouses_gdf, products)
    inventory_df.to_parquet('data/processed/inventory_snapshot.parquet', index=False, compression='snappy')
    print(f"✅ Generated {len(inventory_df):,} inventory records\n")
    
    # Step 7: Disasters (10)
    print("🌋 STEP 7/8: Generating disasters...")
    disasters = generate_disasters()
    with open('data/raw/disasters.json', 'w') as f:
        json.dump(disasters, f, indent=2)
    print(f"✅ Generated {len(disasters)} disaster scenarios\n")
    
    # Step 8: Summary
    print("="*70)
    print("✅ DATA GENERATION COMPLETE!")
    print("="*70)
    print(f"""
📁 Generated Files:
   data/raw/
   ├── products.csv                     ({len(products)} rows)
   ├── factories.geojson                ({len(factories_gdf):,} features)
   ├── ports.geojson                    ({len(ports_gdf):,} features)
   ├── warehouses.geojson               ({len(warehouses_gdf):,} features)
   └── disasters.json                   ({len(disasters)} scenarios)
   
   data/processed/
   ├── routes.parquet                   ({len(routes_df):,} rows, ~15MB)
   └── inventory_snapshot.parquet       ({len(inventory_df):,} rows, ~10MB)

📊 Statistics:
   Total Nodes:     {len(factories_gdf) + len(ports_gdf) + len(warehouses_gdf):,}
   Total Edges:     {len(routes_df):,}
   Products:        {len(products)}
   Disasters:       {len(disasters)}
   
⏱️  Total generation time: ~5-8 minutes
⏱️  Estimated Neo4j load time: 10-15 minutes

🚀 Next Step: Run `python scripts/load_data_to_neo4j.py`
""")

if __name__ == '__main__':
    main()
