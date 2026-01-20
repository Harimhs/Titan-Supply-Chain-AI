"""
Test HyDRA verification system
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.rag.graph_rag import GraphRAG
from src.llm.hydra_verifier import HyDRAVerifier

def test_hydra_verification():
    print("\n" + "="*70)
    print("TEST: HyDRA HALLUCINATION DETECTION")
    print("="*70)
    
    graph_rag = GraphRAG()
    verifier = HyDRAVerifier(graph_rag)
    
    # Get actual cascade data
    cascade_data = graph_rag.get_cascade_path("FAC-00042", "WH-000001")
    
    print(f"\n📊 Actual Cascade Data:")
    print(f"   Distance: {cascade_data['total_distance_km']:.0f} km")
    print(f"   Time: {cascade_data['total_time_days']:.1f} days")
    print(f"   Hops: {cascade_data['hops']}")
    
    # TEST 1: CORRECT LLM output
    print("\n" + "-"*70)
    print("TEST 1: Correct LLM Output (No Hallucinations)")
    print("-"*70)
    
    correct_output = f"""
    The cascade from Taiwan factory to Mumbai warehouse covers {cascade_data['total_distance_km']:.0f} km 
    and takes {cascade_data['total_time_days']:.1f} days through {cascade_data['hops']} hops.
    Estimated impact: $15M in delayed shipments affecting 50 facilities.
    """
    
    result = verifier.verify_cascade_prediction(correct_output, cascade_data)
    
    print(f"\n✅ Verification Result:")
    print(f"   Valid: {result['is_valid']}")
    print(f"   Confidence: {result['confidence']:.2f}")
    print(f"   Violations: {len(result['violations'])}")
    
    # TEST 2: HALLUCINATED LLM output (wrong numbers)
    print("\n" + "-"*70)
    print("TEST 2: Hallucinated LLM Output (Wrong Numbers)")
    print("-"*70)
    
    hallucinated_output = """
    The cascade from Taiwan factory to Mumbai warehouse covers 10,000 km 
    and takes 30 days through 8 hops.
    Estimated impact: $500B in delayed shipments affecting 5000000 facilities.
    """
    
    result = verifier.verify_cascade_prediction(hallucinated_output, cascade_data)
    
    print(f"\n🚨 Verification Result:")
    print(f"   Valid: {result['is_valid']}")
    print(f"   Confidence: {result['confidence']:.2f}")
    print(f"   Violations: {len(result['violations'])}")
    
    if result['violations']:
        print(f"\n   Detected Violations:")
        for v in result['violations']:
            print(f"   ❌ {v['type']}")
            print(f"      Claimed: {v.get('claimed', 'N/A')}")
            print(f"      Actual: {v.get('actual', 'N/A')}")
            if 'error' in v:
                print(f"      Error: {v['error']}")
    
    # TEST 3: Auto-correction
    print("\n" + "-"*70)
    print("TEST 3: Auto-Correction")
    print("-"*70)
    
    corrected = verifier.apply_corrections(hallucinated_output, cascade_data, result['violations'])
    
    print(f"\n📝 Original Output:")
    print(hallucinated_output)
    
    print(f"\n✅ Corrected Output:")
    print(corrected)
    
    graph_rag.close()
    
    print("\n" + "="*70)
    print("✅ HyDRA TEST COMPLETE")
    print("="*70)


if __name__ == "__main__":
    test_hydra_verification()
