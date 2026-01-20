#!/usr/bin/env python3
"""
Live Query Testing
Test the full LLM orchestration pipeline
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.orchestrator.query_orchestrator import QueryOrchestrator
from src.llm.response_generator import ResponseGenerator

def test_live_queries():
    """Test various query types"""
    
    print("\n" + "="*70)
    print("🤖 LIVE QUERY TESTING - LLM ORCHESTRATION")
    print("="*70 + "\n")
    
    orchestrator = QueryOrchestrator()
    generator = ResponseGenerator()
    
    # Test queries
    test_queries = [
        "What is the risk assessment for FACTORY_0001?",
        "Find the best route from FACTORY_0001 to WAREHOUSE_0010",
        "Predict demand for P1 in China",
        "What active disasters are affecting the supply chain?",
        "Show me factories in USA",
        "What is the country risk for China?",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*70}")
        print(f"TEST QUERY {i}/{len(test_queries)}")
        print(f"{'='*70}\n")
        
        # Execute query
        results = orchestrator.execute_query(query)
        
        # Generate response
        response = generator.generate_response(results)
        
        print(response)
        print("\n" + "-"*70)
    
    orchestrator.close()
    
    print("\n" + "="*70)
    print("✅ ALL LIVE QUERIES COMPLETED!")
    print("="*70)

if __name__ == "__main__":
    test_live_queries()
