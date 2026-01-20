"""
Test full integrated system: DCBA + Multi-RAG + HyDRA
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.dcba.integrated_query_engine import IntegratedQueryEngine


def test_full_pipeline():
    print("\n" + "="*70)
    print("🚀 FULL TITAN SYSTEM TEST")
    print("="*70)
    
    engine = IntegratedQueryEngine()
    
    # Test Query 1: Cascade Analysis
    print("\n" + "-"*70)
    print("QUERY 1: Cascade Analysis")
    print("-"*70)
    
    result = engine.query("What is the cascade impact from FAC-00042 to WH-000001?")
    
    print(f"\n📝 Answer:")
    print(result['answer'])
    
    print(f"\n📊 Confidence: {result['confidence']:.2%}")
    
    if result['verification']:
        print(f"\n🛡️  HyDRA Verification:")
        print(f"   Valid: {result['verification']['is_valid']}")
        print(f"   Violations: {len(result['verification']['violations'])}")
    
    # Test Query 2: Product Search
    print("\n" + "-"*70)
    print("QUERY 2: Product Search")
    print("-"*70)
    
    result = engine.query("Find electronics products")
    
    print(f"\n📝 Answer:")
    print(result['answer'])
    
    if result['vector_results']:
        print(f"\n📦 Found Products:")
        for p in result['vector_results'][:3]:
            print(f"   - {p['name']} (SKU: {p['sku']})")
    
    # Test Query 3: Cache test (same query again)
    print("\n" + "-"*70)
    print("QUERY 3: Cache Test (Repeat Query 2)")
    print("-"*70)
    
    result = engine.query("Find electronics products")
    print("   ⚡ Should see 'Cache hit!' above")
    
    engine.close()
    
    print("\n" + "="*70)
    print("✅ FULL SYSTEM TEST COMPLETE!")
    print("="*70)


if __name__ == "__main__":
    test_full_pipeline()
