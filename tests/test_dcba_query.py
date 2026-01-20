"""
Test DCBA System with real queries
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.rag.graph_rag import GraphRAG
from src.rag.vector_rag import VectorRAG
from src.rag.crag import CRAG
from src.rag.rag_cache import RAGCache
from src.dcba.query_analyzer import QueryAnalyzer
from src.dcba.state_manager import StateManager
from src.dcba.allocator import DynamicContextBudgetAllocator
from src.llm.groq_client import GroqClient
from src.llm.prompt_templates import cascade_analysis_prompt

def test_cascade_query():
    """
    Test: "What happens if Taiwan TSMC factory fails?"
    """
    print("\n" + "="*70)
    print("TEST 1: CASCADE ANALYSIS")
    print("="*70)
    
    # Initialize components
    graph_rag = GraphRAG()
    vector_rag = VectorRAG()
    crag = CRAG(graph_rag, vector_rag)
    cache = RAGCache()
    analyzer = QueryAnalyzer()
    state = StateManager()
    allocator = DynamicContextBudgetAllocator()
    
    # Query
    query = "What is the impact if FAC-00042 in Taiwan fails? Show cascade to WH-000001 in Coimbatore"
    
    # Step 1: Analyze query
    print(f"\n📝 Query: {query}")
    analysis = analyzer.analyze(query)
    print(f"\n🔍 Analysis:")
    print(f"   Type: {analysis['type']}")
    print(f"   Complexity: {analysis['complexity']}")
    print(f"   Entities: {analysis['entities']}")
    
    # Step 2: Allocate budget
    allocation = allocator.allocate(analysis, state.get_context())
    print(f"\n💰 Budget Allocation:")
    summary = allocator.get_allocation_summary(allocation)
    for component, budget in summary.items():
        print(f"   {component}: {budget}")
    
    # Step 3: Execute with GraphRAG
    print(f"\n🔄 Executing GraphRAG...")
    cascade_result = graph_rag.get_cascade_path("FAC-00042", "WH-000001")
    
    if cascade_result:
        print(f"\n✅ Found cascade path:")
        print(f"   Hops: {cascade_result['hops']}")
        print(f"   Distance: {cascade_result['total_distance_km']:.0f} km")
        print(f"   Time: {cascade_result['total_time_days']:.1f} days")
        print(f"\n   Path:")
        for node in cascade_result['nodes']:
            print(f"   → {node['name']} ({node['type']}) in {node.get('city', 'N/A')}, {node.get('country', 'N/A')}")
    else:
        print("   ❌ No path found")
    
    # Step 4: Find downstream impact
    print(f"\n🌊 Finding downstream impact...")
    downstream = graph_rag.get_downstream_impact("FAC-00042", max_hops=3)
    print(f"   Affected warehouses: {len(downstream)}")
    if downstream:
        print(f"   Top 3 affected:")
        for wh in downstream[:3]:
            print(f"   - {wh['name']} in {wh['city']}, {wh['country']} ({wh['hops']} hops away)")
    
    # Step 5: Update state
    state.update(analysis, cascade_result)
    
    # Close
    graph_rag.close()
    
    print("\n" + "="*70)
    print("✅ TEST COMPLETE")
    print("="*70)


def test_product_search():
    """
    Test: "Find electronics products from Asia"
    """
    print("\n" + "="*70)
    print("TEST 2: PRODUCT SEARCH (VectorRAG)")
    print("="*70)
    
    vector_rag = VectorRAG()
    analyzer = QueryAnalyzer()
    allocator = DynamicContextBudgetAllocator()
    state = StateManager()
    
    query = "Find electronics products"
    
    print(f"\n📝 Query: {query}")
    analysis = analyzer.analyze(query)
    print(f"   Type: {analysis['type']}")
    
    allocation = allocator.allocate(analysis, state.get_context())
    print(f"\n💰 Budget Allocation:")
    summary = allocator.get_allocation_summary(allocation)
    for component, budget in summary.items():
        print(f"   {component}: {budget}")
    
    print(f"\n🔍 Searching products...")
    results = vector_rag.search_products(query, n_results=3)
    
    if results:
        print(f"   Found {len(results)} products:")
        for p in results:
            print(f"   - {p['name']} ({p['category']}) - SKU: {p['sku']}")
    else:
        print("   ❌ No products found")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    print("\n🚀 TESTING DCBA SYSTEM\n")
    
    try:
        test_cascade_query()
        test_product_search()
        
        print("\n✅ ALL TESTS PASSED!")
        print("\n💡 Next steps:")
        print("   1. Add more test queries")
        print("   2. Build dashboard to visualize this")
        print("   3. Add God Mode for interactive node disabling")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
