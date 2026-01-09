# Quick script to test fixes
# test_fixes.py

from src.rag.graph_rag import GraphRAG

graph_rag = GraphRAG()

print("\n" + "="*70)
print("TESTING FIXES")
print("="*70)

# Test 1: Mumbai warehouses (should now work)
print("\n1️⃣ Mumbai Warehouses:")
context = graph_rag.get_context_for_query("warehouses in mumbai", max_tokens=3000)
if "Warehouses in Mumbai:" in context:
    print("✅ FIXED - Shows Mumbai warehouses")
    print(context[:300])
else:
    print("❌ STILL BROKEN - Shows global stats")
    print(context[:200])

# Test 2: Taiwan earthquake (should prioritize Taiwan)
print("\n2️⃣ Taiwan Earthquake:")
context = graph_rag.get_context_for_query("taiwan earthquake impact", max_tokens=3000)
if "Impact Analysis for Taiwan:" in context:
    print("✅ FIXED - Analyzes Taiwan disaster")
    print(context[:400])
else:
    print("⚠️  PARTIAL - Lists Taiwan but analyzes wrong disaster")
    print(context[:400])

graph_rag.close()
print("\n" + "="*70)
