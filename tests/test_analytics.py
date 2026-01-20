#!/usr/bin/env python3
"""
Test Risk Assessment and Route Optimization
Updated to match the new dynamic logic
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.analytics.risk_engine import RiskAssessmentEngine
from src.analytics.route_optimizer import RouteOptimizer

def test_risk_assessment():
    """Test risk assessment system"""
    print("\n" + "="*70)
    print("TEST 5: Risk Assessment System")
    print("="*70 + "\n")
    
    risk_engine = RiskAssessmentEngine()
    
    # Test 1: Assess specific facility
    # Note: Ensure FACTORY_0001 exists in your graph
    print("Test: Assess facility FACTORY_0001")
    risk = risk_engine.assess_facility_risk("FACTORY_0001")
    
    if 'error' not in risk:
        print(f"  Facility: {risk['name']} ({risk['city']}, {risk['country']})")
        print(f"  Risk Level: {risk['risk_level']} ({risk['overall_risk_score']})")
        print(f"  Components:")
        for component, score in risk['risk_components'].items():
            print(f"    - {component}: {score}")
        print(f"  Recommendations: {len(risk['recommendations'])}")
        for rec in risk['recommendations'][:2]:
            print(f"    • {rec['action']}")
    else:
        print(f"  Error: {risk['error']}")
    print()
    
    # Test 2: Country-level risk
    print("Test: Assess country risk for China")
    country_risk = risk_engine.assess_country_risk("China")
    
    if 'error' not in country_risk:
        print(f"  Total facilities: {country_risk['total_facilities']}")
        print(f"  Average risk: {country_risk['average_risk_score']}")
        print(f"  High risk facilities: {country_risk['high_risk_facilities']}")
    else:
        print(f"  Error: {country_risk['error']}")
    print()
    
    risk_engine.close()

def test_route_optimization():
    """Test route optimization system"""
    print("="*70)
    print("TEST 6: Route Optimization System")
    print("="*70 + "\n")
    
    route_optimizer = RouteOptimizer()
    
    # Test 1: Find alternative routes
    print("Test: Find routes from FACTORY_0001 to WAREHOUSE_0010")
    # Ensure these IDs exist in your graph
    routes = route_optimizer.find_alternative_routes("FACTORY_0001", "WAREHOUSE_0010", max_routes=3)
    
    print(f"  Found {len(routes)} alternative routes:")
    for route in routes:
        breakdown = route['time_breakdown']
        print(f"    Route {route['route_number']}: {route['num_hops']} hops, {route['total_distance_km']} km")
        print(f"      Time: {route['estimated_time_days']} days (Travel: {breakdown['travel_days']}, Border: {breakdown['border_delays']})")
        print(f"      Terrain: {breakdown['terrain_type']}")
    print()
    
    # Test 2: Best route recommendation
    print("Test: Recommend best route (time criteria)")
    best = route_optimizer.recommend_best_route("FACTORY_0001", "WAREHOUSE_0010", criteria="time")
    
    if 'error' not in best:
        print(f"  Recommended: Route {best['route_number']}")
        print(f"  Reason: {best['recommendation_reason']}")
        print(f"  Time: {best['estimated_time_days']} days")
    else:
        print(f"  {best['error']}")
    print()
    
    # Test 3: Nearest warehouse (FIXED: Uses Lat/Lon now)
    # Using Coordinates for New York City (approx)
    customer_lat = 40.7128
    customer_lon = -74.0060
    print(f"Test: Find nearest warehouses with P1 for Customer at ({customer_lat}, {customer_lon})")
    
    warehouses = route_optimizer.find_nearest_warehouse("P1", customer_lat, customer_lon, limit=3)
    
    print(f"  Found {len(warehouses)} warehouses:")
    for wh in warehouses:
        print(f"    {wh['name']} - {wh['location']}")
        print(f"      Distance: {wh['distance_km']} km")
        print(f"      Delivery Estimate: {wh['estimated_delivery_days']} days")
    print()
    
    # Test 4: Route diversification
    print("Test: Route diversification for FACTORY_0001")
    diversification = route_optimizer.suggest_route_diversification("FACTORY_0001")
    
    if 'error' not in diversification:
        print(f"  Current routes: {diversification['current_routes']}")
        print(f"  Countries served: {diversification['countries_served']}")
        print(f"  Diversity score: {diversification['diversity_score']}")
        print(f"  Suggestions:")
        for sug in diversification['suggestions']:
            print(f"    [{sug['priority']}] {sug['recommendation']}")
    print()
    
    route_optimizer.close()

def main():
    """Run all analytics tests"""
    try:
        test_risk_assessment()
        test_route_optimization()
        
        print("="*70)
        print("✅ ALL ANALYTICS TESTS COMPLETED!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()