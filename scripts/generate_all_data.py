#!/usr/bin/env python3
"""
Master script to generate ALL synthetic supply chain data
Updated to match new data generation structure
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    """Generate all data in correct order"""
    print("\n" + "="*70)
    print("🌍 TITAN Data Generation - Complete Pipeline")
    print("="*70 + "\n")
    
    # Step 1: Geography (must be first!)
    print("STEP 1/3: Generating Geography...")
    print("-" * 70)
    from data.synthetic.generate_geography import main as generate_geography
    generate_geography()
    print("✅ Geography complete!\n")
    
    # Step 2: Supply Chain (needs geography data)
    print("STEP 2/3: Generating Supply Chain...")
    print("-" * 70)
    from data.synthetic.generate_supply_chain import main as generate_supply_chain
    generate_supply_chain()
    print("✅ Supply Chain complete!\n")
    
    # Step 3: Disruptions (needs all entities)
    print("STEP 3/3: Generating Disruptions...")
    print("-" * 70)
    from data.synthetic.generate_disruptions import main as generate_disruptions
    generate_disruptions()
    print("✅ Disruptions complete!\n")
    
    # Summary
    print("="*70)
    print("🎉 ALL DATA GENERATION COMPLETE!")
    print("="*70)
    print("\n📁 Generated files in data/processed/:")
    print("   ✓ factories.csv")
    print("   ✓ ports.csv")
    print("   ✓ warehouses.csv")
    print("   ✓ products.csv")
    print("   ✓ supply_relationships.csv")
    print("   ✓ stock_relationships.csv")
    print("   ✓ disasters.csv")
    print("\n🚀 Next steps:")
    print("   1. Load data to Neo4j: python scripts/load_data_to_neo4j.py")
    print("   2. Create embeddings: python scripts/create_embeddings.py")
    print("   3. Start dashboard: python src/dashboard/dashboard_api.py")
    print()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error during data generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
