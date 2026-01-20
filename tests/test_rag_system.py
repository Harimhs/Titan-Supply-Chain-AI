#!/usr/bin/env python3
"""
Comprehensive RAG Integration Tests
Tests all RAG components with NEW data
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.rag.vector_rag import VectorRAG
from src.graph.neo4j_client import Neo4jClient
from src.rag.ml_predictor import DemandPredictor

class RAGIntegrationTester:
    """Test all RAG components"""
    
    def __init__(self):
        """Initialize all components"""
        print("\n" + "="*70)
        print("🧪 RAG INTEGRATION TEST SUITE")
        print("="*70 + "\n")
        
        try:
            self.vector_rag = VectorRAG()
            self.graph_client = Neo4jClient()
            self.ml_predictor = DemandPredictor()
            print("✅ All components initialized\n")
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            raise
    
    def test_vector_search(self):
        """Test vector search across all collections"""
        print("="*70)
        print("TEST 1: Vector Search")
        print("="*70 + "\n")
        
        test_queries = [
            "electronics semiconductors",
            "earthquake disaster impact",
            "automotive factory China"
        ]
        
        for query in test_queries:
            print(f"Query: '{query}'")
            results = self.vector_rag.search_all(query, n_results=2)
            
            print(f"  Products found: {len(results['products'])}")
            print(f"  Disasters found: {len(results['disasters'])}")
            print(f"  Factories found: {len(results['factories'])}")
            
            if results['products']:
                print(f"  Top product: {results['products'][0]['metadata']['name']}")
            
            print()
    
    def test_graph_queries(self):
        """Test Neo4j graph queries"""
        print("="*70)
        print("TEST 2: Graph Queries")
        print("="*70 + "\n")
        
        # Test 1: Get factories by country
        print("Query: Factories in China")
        factories = self.graph_client.get_factories_by_country("China", limit=3)
        print(f"  Found {len(factories)} factories")
        if factories:
            print(f"  Sample: {factories[0]['f']['name']}")
        print()
        
        # Test 2: Get factories by product
        print("Query: Factories producing P1 (Electronics)")
        factories = self.graph_client.get_factories_by_product("P1", limit=3)
        print(f"  Found {len(factories)} factories")
        if factories:
            print(f"  Sample: {factories[0]['f']['name']} in {factories[0]['f']['city']}")
        print()
        
        # Test 3: Get active disasters
        print("Query: Active disasters")
        disasters = self.graph_client.get_active_disasters()
        print(f"  Found {len(disasters)} active disasters")
        if disasters:
            print(f"  Sample: {disasters[0]['d']['type']} in {disasters[0]['d']['country']}")
        print()
        
        # Test 4: Country statistics
        print("Query: Supply chain stats for USA")
        stats = self.graph_client.get_country_supply_chain_stats("USA")
        if stats:
            print(f"  Factories: {stats[0]['num_factories']}")
            print(f"  Supply routes: {stats[0]['num_supply_routes']}")
            print(f"  Total capacity: {stats[0]['total_capacity']}")
        print()
    
    def test_ml_predictions(self):
        """Test ML demand predictions"""
        print("="*70)
        print("TEST 3: ML Demand Predictions")
        print("="*70 + "\n")
        
        test_cases = [
            {"product_id": "P1", "country": "China", "lag_1_demand": 1200},
            {"product_id": "P2", "country": "USA", "lag_1_demand": 600},
            {"product_id": "P5", "country": "India", "lag_1_demand": 1800}
        ]
        
        for case in test_cases:
            prediction = self.ml_predictor.predict(**case)
            print(f"Product: {case['product_id']}, Country: {case['country']}")
            print(f"  Predicted demand: {prediction['predicted_demand']:,}")
            print(f"  Range: {prediction['lower_bound']:,} - {prediction['upper_bound']:,}")
            print()
    
    def test_disaster_impact_analysis(self):
        """Test disaster impact queries"""
        print("="*70)
        print("TEST 4: Disaster Impact Analysis")
        print("="*70 + "\n")
        
        # Get a disaster and analyze its impacts
        disasters = self.graph_client.get_active_disasters()
        
        if disasters:
            disaster = disasters[0]['d']
            print(f"Analyzing: {disaster['type']} in {disaster['country']}")
            print(f"Severity: {disaster['severity']}")
            
            # Get affected entities
            impacts = self.graph_client.get_disaster_impacts(disaster['id'])
            print(f"  Affected entities: {len(impacts)}")
            
            if impacts:
                entity_types = {}
                for impact in impacts:
                    entity_type = impact['entity_type'][0]
                    entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
                
                for entity_type, count in entity_types.items():
                    print(f"    {entity_type}: {count}")
        else:
            print("  No active disasters found")
        
        print()
    
    def run_all_tests(self):
        """Run complete test suite"""
        try:
            self.test_vector_search()
            self.test_graph_queries()
            self.test_ml_predictions()
            self.test_disaster_impact_analysis()
            
            print("="*70)
            print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
            print("="*70)
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self.graph_client.close()

def main():
    """Run test suite"""
    tester = RAGIntegrationTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
