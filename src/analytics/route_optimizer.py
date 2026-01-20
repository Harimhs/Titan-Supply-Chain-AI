#!/usr/bin/env python3
"""
Supply Chain Route Optimization - FIXED VERSION
Realistic route calculations with terrain and border delays
"""
import sys
from pathlib import Path
import math

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.graph.neo4j_client import Neo4jClient

class RouteOptimizer:
    """Find and recommend optimal supply chain routes"""
    
    def __init__(self):
        """Initialize route optimizer"""
        self.neo4j_client = Neo4jClient()
        
        # FIXED: Terrain-adjusted speed (km/day)
        self.terrain_speed = {
            "highway": 600,      # Modern highways
            "standard": 450,     # Regular roads
            "mountainous": 300,  # Mountain regions
            "coastal": 500       # Coastal routes
        }
        
        # FIXED: Border crossing delays (days)
        self.border_delay = {
            "domestic": 0,
            "friendly": 1,     # EU, USMCA, etc.
            "standard": 2,     # Normal customs
            "strict": 4        # Complex customs
        }
        
        # Country groupings for border delay estimation
        self.trade_blocs = {
            "EU": ["Germany", "France", "Italy", "Poland", "UK"],
            "USMCA": ["USA", "Canada"],
            "ASEAN": ["Singapore"],
            "Developed": ["Japan", "South Korea", "Australia"]
        }
        
        print("✅ Route Optimizer initialized")
    
    def _estimate_terrain(self, source_country, dest_country):
        """Estimate terrain type based on countries"""
        # Simplified terrain estimation
        mountainous_countries = ["Argentina", "South Africa", "Egypt"]
        coastal_countries = ["Japan", "South Korea", "Singapore", "UK", "Australia"]
        
        if source_country in mountainous_countries or dest_country in mountainous_countries:
            return "mountainous"
        elif source_country in coastal_countries or dest_country in coastal_countries:
            return "coastal"
        elif source_country in ["USA", "Germany", "China"]:
            return "highway"
        else:
            return "standard"
    
    def _calculate_border_delay(self, source_country, dest_country):
        """
        FIXED: Calculate realistic border crossing delay
        """
        # Same country = no delay
        if source_country == dest_country:
            return self.border_delay["domestic"]
        
        # Check if both in same trade bloc
        for bloc, countries in self.trade_blocs.items():
            if source_country in countries and dest_country in countries:
                return self.border_delay["friendly"]
        
        # Developed to developed = standard
        all_developed = (
            self.trade_blocs["Developed"] + 
            self.trade_blocs["EU"] + 
            self.trade_blocs["USMCA"]
        )
        
        if source_country in all_developed and dest_country in all_developed:
            return self.border_delay["standard"]
        
        # Involving Russia, Egypt, Argentina = stricter
        strict_countries = ["Russia", "Egypt", "Argentina", "Brazil"]
        if source_country in strict_countries or dest_country in strict_countries:
            return self.border_delay["strict"]
        
        # Default
        return self.border_delay["standard"]
    
    def _estimate_transit_time(self, distance_km, num_hops, route_nodes):
        """
        FIXED: Realistic transit time estimation
        """
        # Extract countries from route
        countries = []
        for node in route_nodes:
            # Get country from Neo4j if needed
            query = "MATCH (n {id: $id}) RETURN n.country as country"
            result = self.neo4j_client.run_query(query, {"id": node['id']})
            if result:
                countries.append(result[0].get('country', 'Unknown'))
        
        # Estimate terrain
        if len(countries) >= 2:
            terrain = self._estimate_terrain(countries[0], countries[-1])
        else:
            terrain = "standard"
        
        # Calculate travel time based on terrain
        speed = self.terrain_speed.get(terrain, 450)
        travel_days = distance_km / speed
        
        # FIXED: Calculate border delays
        total_border_delay = 0
        for i in range(len(countries) - 1):
            delay = self._calculate_border_delay(countries[i], countries[i+1])
            total_border_delay += delay
        
        # Handling time per hop (loading/unloading)
        handling_days = num_hops * 0.5  # 12 hours per stop
        
        total_days = travel_days + total_border_delay + handling_days
        
        return {
            "total_days": round(total_days, 1),
            "travel_days": round(travel_days, 1),
            "border_delays": round(total_border_delay, 1),
            "handling_days": round(handling_days, 1),
            "terrain_type": terrain
        }
    
    def find_alternative_routes(self, source_id, destination_id, avoid_ids=None, max_routes=3):
        routes = []
    
        for route_num in range(max_routes):
            # FIX: Initialize avoid_ids as empty list if not set
            avoid_ids = [] if route_num == 0 else [r['nodes'][1:-1] for r in routes if 'nodes' in r]
            
            # FIX: Flatten avoid_ids if nested
            if avoid_ids and isinstance(avoid_ids[0], list):
                avoid_ids = [item for sublist in avoid_ids for item in sublist]
            
            # FIX: Ensure avoid_ids is always a list
            if not isinstance(avoid_ids, list):
                avoid_ids = []
            
            # NOW this line will work:
            avoid_list = ", ".join([f"'{id}'" for id in avoid_ids])
        avoid_clause = ""
        if avoid_ids:
            avoid_list = ", ".join([f"'{id}'" for id in avoid_ids])
            avoid_clause = f"WHERE NONE(n IN nodes(path) WHERE n.id IN [{avoid_list}])"
        
        query = f"""
        MATCH path = (source {{id: $source_id}})-[:SUPPLIES_TO*1..5]->(dest {{id: $dest_id}})
        {avoid_clause}
        WITH path, 
             reduce(dist = 0, r IN relationships(path) | dist + r.distance_km) as total_distance,
             reduce(cost = 0, r IN relationships(path) | cost + r.quantity) as total_volume
        RETURN 
            [n IN nodes(path) | {{id: n.id, type: labels(n)[0], name: n.name, country: n.country}}] as route_nodes,
            total_distance,
            total_volume,
            length(path) as num_hops
        ORDER BY total_distance
        LIMIT $max_routes
        """
        
        results = self.neo4j_client.run_query(query, {
            "source_id": source_id,
            "dest_id": destination_id,
            "max_routes": max_routes
        })
        
        routes = []
        for idx, result in enumerate(results):
            # FIXED: Use realistic time estimation
            time_breakdown = self._estimate_transit_time(
                result['total_distance'],
                result['num_hops'],
                result['route_nodes']
            )
            
            routes.append({
                "route_number": idx + 1,
                "nodes": result['route_nodes'],
                "total_distance_km": round(result['total_distance'], 1),
                "num_hops": result['num_hops'],
                "estimated_time_days": time_breakdown['total_days'],
                "time_breakdown": time_breakdown,
                "route_type": self._classify_route(result['num_hops'])
            })
        
        return routes
    
    def _classify_route(self, num_hops):
        """Classify route based on complexity"""
        if num_hops <= 2:
            return "Direct"
        elif num_hops <= 4:
            return "Indirect"
        else:
            return "Complex"
    
    def recommend_best_route(self, source_id, destination_id, criteria="distance"):
        """Recommend single best route based on criteria"""
        routes = self.find_alternative_routes(source_id, destination_id, max_routes=5)
        
        if not routes:
            return {"error": "No route found"}
        
        if criteria == "distance":
            best_route = min(routes, key=lambda r: r['total_distance_km'])
            reason = f"Shortest distance: {best_route['total_distance_km']} km"
        elif criteria == "time":
            best_route = min(routes, key=lambda r: r['estimated_time_days'])
            reason = f"Fastest delivery: {best_route['estimated_time_days']} days"
        elif criteria == "hops":
            best_route = min(routes, key=lambda r: r['num_hops'])
            reason = f"Fewest hops: {best_route['num_hops']} stops"
        else:
            best_route = routes[0]
            reason = "Default recommendation"
        
        return {
            **best_route,
            "recommendation_reason": reason,
            "alternative_routes_available": len(routes) - 1
        }
    
    def find_nearest_warehouse(self, product_id, customer_lat, customer_lon, limit=3):
        """
        FIXED: Find nearest warehouses based on CUSTOMER location
        
        Args:
            product_id: Product to search for
            customer_lat: Customer latitude
            customer_lon: Customer longitude
            limit: Number of results
        """
        query = """
        MATCH (w:Warehouse)-[:STOCKS]->(p:Product {id: $product_id})
        WITH w, 
             point.distance(
                 point({latitude: w.lat, longitude: w.lon}),
                 point({latitude: $customer_lat, longitude: $customer_lon})
             ) / 1000 as distance_km
        RETURN DISTINCT w.id as warehouse_id, 
               w.name as warehouse_name,
               w.city as city,
               w.country as country,
               w.lat as lat,
               w.lon as lon,
               distance_km
        ORDER BY distance_km
        LIMIT $limit
        """
        
        results = self.neo4j_client.run_query(query, {
            "product_id": product_id,
            "customer_lat": customer_lat,
            "customer_lon": customer_lon,
            "limit": limit
        })
        
        # FIXED: Calculate realistic delivery time
        warehouses = []
        for r in results:
            # Estimate terrain and speed
            speed = 450  # Average km/day
            travel_days = r['distance_km'] / speed
            handling_days = 2  # Warehouse processing + last mile
            
            warehouses.append({
                "warehouse_id": r['warehouse_id'],
                "name": r['warehouse_name'],
                "location": f"{r['city']}, {r['country']}",
                "distance_km": round(r['distance_km'], 1),
                "estimated_delivery_days": round(travel_days + handling_days, 1)
            })
        
        return warehouses
    
    def suggest_route_diversification(self, facility_id):
        """Suggest route diversification strategies"""
        routes = self.neo4j_client.get_factory_supply_routes(facility_id)
        
        if not routes:
            return {"error": "No routes found for this facility"}
        
        destinations = set()
        destination_countries = set()
        
        for route in routes:
            dest = route['destination']
            destinations.add(dest['id'])
            destination_countries.add(dest.get('country', 'Unknown'))
        
        num_routes = len(routes)
        num_countries = len(destination_countries)
        
        diversity_score = min(1.0, (num_routes * 0.2) + (num_countries * 0.3))
        
        suggestions = []
        
        if num_routes < 3:
            suggestions.append({
                "priority": "High",
                "recommendation": "Establish additional supply routes",
                "reason": f"Currently only {num_routes} routes - target is 3+",
                "action": "Identify backup ports and warehouses"
            })
        
        if num_countries < 2:
            suggestions.append({
                "priority": "Medium",
                "recommendation": "Diversify geographic destinations",
                "reason": "All routes go to same country - geographic concentration risk",
                "action": "Explore cross-border supply options"
            })
        
        if diversity_score < 0.5:
            suggestions.append({
                "priority": "High",
                "recommendation": "Improve route redundancy",
                "reason": f"Diversity score is {diversity_score:.2f} (below 0.5 threshold)",
                "action": "Create backup routes to different regions"
            })
        
        if not suggestions:
            suggestions.append({
                "priority": "Low",
                "recommendation": "Maintain current diversification",
                "reason": f"Good route diversity: {num_routes} routes across {num_countries} countries",
                "action": "Continue monitoring and periodic review"
            })
        
        return {
            "facility_id": facility_id,
            "current_routes": num_routes,
            "countries_served": num_countries,
            "diversity_score": round(diversity_score, 2),
            "suggestions": suggestions
        }
    
    def close(self):
        """Close connections"""
        self.neo4j_client.close()
