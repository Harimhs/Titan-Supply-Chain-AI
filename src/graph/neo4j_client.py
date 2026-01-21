#!/usr/bin/env python3
"""
Neo4j Graph Database Client - COMPLETE VERSION
All facility type queries
"""
import os
import logging
from neo4j import GraphDatabase
from typing import List, Dict, Any

logging.getLogger("neo4j").setLevel(logging.ERROR)

class Neo4jClient:
    """Neo4j database operations"""
    
    def __init__(self):
        """
        Initialize Neo4j connection with CLOUD SAFETY NET
        """
        # 1. URI LOGIC: Check Env, otherwise force Cloud
        env_uri = os.getenv("NEO4J_URI", "")
        if not env_uri or "localhost" in env_uri:
            print("⚠️ Cloud Environment detected with missing/local URI. Switching to Fallback.")
            self.uri = "neo4j+s://9a2bef51.databases.neo4j.io"
        else:
            self.uri = env_uri

        # 2. AUTH LOGIC: Check Env, otherwise force Cloud Password
        # We check NEO4J_USERNAME (and NEO4J_USER for safety)
        self.user = os.getenv("NEO4J_USERNAME", os.getenv("NEO4J_USER", "neo4j"))
        
        env_pass = os.getenv("NEO4J_PASSWORD", "")
        if not env_pass:
            print("⚠️ No Password Variable found. Using Hardcoded Cloud Password.")
            self.password = "1HtTwO8Hic-bMo14JFt-YPbopAU24OJU4UUGOPO0978"
        else:
            self.password = env_pass

        # 3. CONNECT
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            self.driver.verify_connectivity()
            print(f"✅ Neo4j Client Connected to: {self.uri}")
        except Exception as e:
            print(f"❌ Neo4j Connection Failed: {e}")
            self.driver = None
    
    def close(self):
        """Close connection"""
        self.driver.close()
    
    def run_query(self, query, parameters=None):
        """Execute Cypher query"""
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]
    
    # === ENTITY QUERIES ===
    
    def get_factory_by_id(self, factory_id):
        """Get factory details"""
        query = """
        MATCH (f:Factory {id: $factory_id})
        RETURN f
        """
        return self.run_query(query, {"factory_id": factory_id})
    
    def get_factories_by_country(self, country, limit=10):
        """Get factories in a country"""
        query = """
        MATCH (f:Factory {country: $country})
        RETURN f
        LIMIT $limit
        """
        return self.run_query(query, {"country": country, "limit": limit})
    
    # FIXED: Add warehouse queries
    def get_warehouses_by_country(self, country, limit=10):
        """Get warehouses in a country"""
        query = """
        MATCH (w:Warehouse {country: $country})
        RETURN w
        LIMIT $limit
        """
        return self.run_query(query, {"country": country, "limit": limit})
    
    # FIXED: Add port queries
    def get_ports_by_country(self, country, limit=10):
        """Get ports in a country"""
        query = """
        MATCH (p:Port {country: $country})
        RETURN p
        LIMIT $limit
        """
        return self.run_query(query, {"country": country, "limit": limit})
    
    def get_factories_by_product(self, product_id, limit=10):
        """Get factories producing a product"""
        query = """
        MATCH (f:Factory {product_type: $product_id})
        RETURN f
        LIMIT $limit
        """
        return self.run_query(query, {"product_id": product_id, "limit": limit})
    
    def get_port_by_id(self, port_id):
        """Get port details"""
        query = """
        MATCH (p:Port {id: $port_id})
        RETURN p
        """
        return self.run_query(query, {"port_id": port_id})
    
    def get_warehouse_by_id(self, warehouse_id):
        """Get warehouse details"""
        query = """
        MATCH (w:Warehouse {id: $warehouse_id})
        RETURN w
        """
        return self.run_query(query, {"warehouse_id": warehouse_id})
    
    # === SUPPLY CHAIN QUERIES ===
    
    def get_supply_chain_path(self, start_id, end_id, max_hops=5):
        """Find supply chain path between two entities"""
        query = """
        MATCH path = shortestPath(
            (start {id: $start_id})-[:SUPPLIES_TO*1..%d]->(end {id: $end_id})
        )
        RETURN path
        """ % max_hops
        return self.run_query(query, {"start_id": start_id, "end_id": end_id})
    
    def get_factory_supply_routes(self, factory_id):
        """Get all supply routes from a factory"""
        query = """
        MATCH (f:Factory {id: $factory_id})-[r:SUPPLIES_TO]->(destination)
        RETURN f, r, destination
        """
        return self.run_query(query, {"factory_id": factory_id})
    
    def get_warehouse_stock(self, warehouse_id):
        """Get products stocked in warehouse"""
        query = """
        MATCH (w:Warehouse {id: $warehouse_id})-[s:STOCKS]->(p:Product)
        RETURN w, s, p
        """
        return self.run_query(query, {"warehouse_id": warehouse_id})
    
    # === DISASTER IMPACT QUERIES ===
    
    def get_disaster_impacts(self, disaster_id):
        """Get entities affected by a disaster"""
        query = """
        MATCH (d:Disaster {id: $disaster_id})-[a:AFFECTS]->(entity)
        RETURN d, a, entity, labels(entity) as entity_type
        """
        return self.run_query(query, {"disaster_id": disaster_id})
    
    def get_disasters_near_facility(self, facility_id, radius_km=500):
        """Get disasters near a facility"""
        query = """
        MATCH (f {id: $facility_id}), (d:Disaster)
        WITH f, d, 
             point.distance(
                 point({latitude: f.lat, longitude: f.lon}),
                 point({latitude: d.lat, longitude: d.lon})
             ) / 1000 as distance_km
        WHERE distance_km <= $radius_km
        RETURN d, distance_km
        ORDER BY distance_km
        """
        return self.run_query(query, {"facility_id": facility_id, "radius_km": radius_km})
    
    def get_active_disasters(self):
        """Get all active disasters"""
        query = """
        MATCH (d:Disaster {status: 'Active'})
        RETURN d
        """
        return self.run_query(query)
    
    # === ANALYTICS QUERIES ===
    
    def get_country_supply_chain_stats(self, country):
        """Get supply chain statistics for a country"""
        query = """
        MATCH (f:Factory {country: $country})
        OPTIONAL MATCH (f)-[r:SUPPLIES_TO]->()
        RETURN 
            $country as country,
            count(DISTINCT f) as num_factories,
            count(r) as num_supply_routes,
            sum(f.capacity) as total_capacity
        """
        return self.run_query(query, {"country": country})
    
    def get_product_supply_network(self, product_id, limit=50):
        """
        FIXED: Get full supply network with proper structure
        Returns simplified format for easier parsing
        """
        query = """
        MATCH (f:Factory {product_type: $product_id})-[r:SUPPLIES_TO]->(destination)
        RETURN 
            f.id as factory_id,
            f.name as factory_name,
            f.city as factory_city,
            f.country as factory_country,
            destination.id as dest_id,
            destination.name as dest_name,
            labels(destination)[0] as dest_type,
            r.distance_km as distance
        LIMIT $limit
        """
        return self.run_query(query, {"product_id": product_id, "limit": limit})
    
    def get_high_risk_facilities(self, min_disaster_count=2):
        """Get facilities affected by multiple disasters"""
        query = """
        MATCH (d:Disaster)-[:AFFECTS]->(f)
        WITH f, count(d) as disaster_count, labels(f) as facility_type
        WHERE disaster_count >= $min_count
        RETURN f, disaster_count, facility_type
        ORDER BY disaster_count DESC
        """
        return self.run_query(query, {"min_count": min_disaster_count})
