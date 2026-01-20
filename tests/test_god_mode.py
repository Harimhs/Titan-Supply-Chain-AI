"""
Test God Mode functionality
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.simulation.god_mode import GodMode

def test_god_mode():
    print("\n" + "="*70)
    print("🎮 GOD MODE TEST")
    print("="*70)
    
    god = GodMode()
    
    # Test 1: Disable a node
    print("\n" + "-"*70)
    print("TEST 1: Disable Factory")
    print("-"*70)
    
    result = god.disable_node("FAC-00042", reason="Testing God Mode")
    print(f"\n✅ Disabled: {result['name']} ({result['type']})")
    
    # Test 2: Check cascade with disabled node
    print("\n" + "-"*70)
    print("TEST 2: Find Alternate Path")
    print("-"*70)
    
    cascade = god.get_cascade_with_disabled("FAC-00042", "WH-000001")
    if cascade['found_path']:
        print(f"✅ Found alternate path with {cascade['hops']} hops")
    else:
        print(f"❌ No path found: {cascade['reason']}")
    
    # Test 3: Find affected warehouses
    print("\n" + "-"*70)
    print("TEST 3: Find Affected Warehouses")
    print("-"*70)
    
    affected = god.get_affected_warehouses_by_disabled_node("FAC-00042")
    print(f"⚠️  {len(affected)} warehouses affected by disabling FAC-00042")
    if affected:
        print("Top 3:")
        for wh in affected[:3]:
            print(f"   - {wh['warehouse_name']} in {wh['city']}, {wh['country']}")
    
    # Test 4: Simulate disaster
    print("\n" + "-"*70)
    print("TEST 4: Simulate Earthquake")
    print("-"*70)
    
    disaster = god.simulate_disaster("Earthquake 7.2", 22.5431, 114.0579, radius_km=50)
    print(f"🌋 Earthquake affected {disaster['affected_count']} facilities")
    
    # Test 5: Get all disabled
    print("\n" + "-"*70)
    print("TEST 5: List All Disabled Nodes")
    print("-"*70)
    
    disabled = god.get_disabled_nodes()
    print(f"📋 Total disabled: {len(disabled)}")
    
    # Test 6: Reset
    print("\n" + "-"*70)
    print("TEST 6: Reset All")
    print("-"*70)
    
    reset = god.reset_all()
    print(f"♻️  Re-enabled {reset['re_enabled']} nodes")
    
    god.close()
    
    print("\n" + "="*70)
    print("✅ GOD MODE TEST COMPLETE")
    print("="*70)


if __name__ == "__main__":
    test_god_mode()
