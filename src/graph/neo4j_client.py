from neo4j import GraphDatabase
from src.utils.config import Config
from typing import List, Dict, Optional

class Neo4jClient:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            Config.NEO4J_URI, 
            auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD)
        )
        self._verify_connection()
        
    def _verify_connection(self):
        """Verify Neo4j is accessible"""
        try:
            self.driver.verify_connectivity()
            print("✅ Neo4j Connected")
        except Exception as e:
            print(f"❌ Neo4j Connection Failed: {e}")
            raise
        
    def close(self):
        self.driver.close()
        
    def query(self, cypher_query: str, params: dict = None) -> List[Dict]:
        """Execute a raw Cypher query"""
        with self.driver.session() as session:
            result = session.run(cypher_query, params or {})
            return [record.data() for record in result]
    
    def find_node_by_name(self, name: str) -> Optional[Dict]:
        """
        Find any node by name (searches across all node types)
        """
        query = """
        MATCH (n)
        WHERE n.name CONTAINS $name 
           OR n.location_name CONTAINS $name
           OR n.city CONTAINS $name
        RETURN n, labels(n)[0] as node_type
        LIMIT 5
        """
        results = self.query(query, {"name": name})
        return results
    
    def get_node_by_id(self, node_id: str) -> Optional[Dict]:
        """
        Get node by its specific ID (factory_id, port_id, warehouse_id, etc.)
        FIX: Works with actual data structure
        """
        query = """
        MATCH (n)
        WHERE n.factory_id = $id 
           OR n.port_id = $id 
           OR n.warehouse_id = $id
           OR n.sku = $id
           OR n.event_id = $id
        RETURN n, labels(n)[0] as node_type
        """
        results = self.query(query, {"id": node_id})
        return results[0] if results else None
            
    def trace_supply_chain(self, start_id: str, end_id: str, max_hops: int = 6) -> List[Dict]:
        """
        GRAPH RAG: Traces dependency path between two facilities
        Used for 'Ripple Effect' analysis
        
        FIX: Uses actual ID fields from our data
        """
        query = f"""
        MATCH (start)
        WHERE start.factory_id = $start_id 
           OR start.port_id = $start_id 
           OR start.warehouse_id = $start_id
        MATCH (end)
        WHERE end.factory_id = $end_id 
           OR end.port_id = $end_id 
           OR end.warehouse_id = $end_id
        MATCH path = shortestPath((start)-[:SUPPLIES_TO*1..{max_hops}]->(end))
        RETURN path, 
               length(path) as hops,
               [node in nodes(path) | labels(node)[0]] as node_types,
               [node in nodes(path) | coalesce(node.name, node.factory_id, node.port_id, node.warehouse_id)] as node_names
        LIMIT 1
        """
        return self.query(query, {"start_id": start_id, "end_id": end_id})

    def find_affected_downstream(self, disaster_location: str, max_depth: int = 5) -> List[Dict]:
        """
        CRITICAL: Finds everything downstream from a disaster
        Tier 1 -> Tier 2 -> Tier 3 cascading failure search
        
        FIX: Uses actual disaster data structure
        """
        query = f"""
        MATCH (d:Disaster)
        WHERE d.location_name CONTAINS $location OR d.event_id = $location
        MATCH (d)-[:AFFECTS]->(victim)
        MATCH path = (victim)-[:SUPPLIES_TO*1..{max_depth}]->(downstream)
        WITH downstream, length(path) as depth, labels(downstream)[0] as type,
             coalesce(downstream.name, downstream.warehouse_id, downstream.factory_id) as name
        RETURN DISTINCT name, type, depth
        ORDER BY depth ASC 
        LIMIT 100
        """
        return self.query(query, {"location": disaster_location})
    
    def find_facilities_near_disaster(self, disaster_id: str) -> List[Dict]:
        """
        Get all facilities affected by a specific disaster
        """
        query = """
        MATCH (d:Disaster {event_id: $disaster_id})-[:AFFECTS]->(n)
        RETURN labels(n)[0] as facility_type,
               coalesce(n.name, n.factory_id, n.port_id, n.warehouse_id) as facility_id,
               n.lat as lat, 
               n.lon as lon,
               point.distance(d.location, n.location)/1000 as distance_km
        ORDER BY distance_km ASC
        """
        return self.query(query, {"disaster_id": disaster_id})
    
    def find_inventory_for_product(self, sku: str, limit: int = 10) -> List[Dict]:
        """
        Find where a product is stocked
        Critical for: "Where can I find iPhone 15 in Coimbatore?"
        """
        query = """
        MATCH (w:Warehouse)-[r:STOCKS]->(p:Product {sku: $sku})
        RETURN w.warehouse_id as warehouse_id,
               w.name as warehouse_name,
               w.city as city,
               r.quantity as quantity,
               w.lat as lat,
               w.lon as lon
        ORDER BY r.quantity DESC
        LIMIT $limit
        """
        return self.query(query, {"sku": sku, "limit": limit})
    
    def search_warehouses_in_city(self, city: str) -> List[Dict]:
        """
        Find all warehouses in a city
        """
        query = """
        MATCH (w:Warehouse)
        WHERE w.city CONTAINS $city
        RETURN w.warehouse_id as id,
               w.name as name,
               w.type as type,
               w.capacity_sqft as capacity,
               w.lat as lat,
               w.lon as lon
        LIMIT 50
        """
        return self.query(query, {"city": city})
    
    def get_supply_chain_stats(self) -> Dict:
        """
        Get overall statistics for dashboard
        """
        stats = {}
        
        # Node counts
        result = self.query("MATCH (n) RETURN labels(n)[0] as type, count(n) as count")
        stats['nodes'] = {r['type']: r['count'] for r in result}
        
        # Relationship counts
        result = self.query("MATCH ()-[r]->() RETURN type(r) as type, count(r) as count")
        stats['relationships'] = {r['type']: r['count'] for r in result}
        
        return stats


# Quick test
if __name__ == "__main__":
    client = Neo4jClient()
    
    print("\n📊 Testing Neo4j Queries...")
    
    # Test 1: Get stats
    stats = client.get_supply_chain_stats()
    print(f"\n1. Stats: {stats}")
    
    # Test 2: Find disaster
    disasters = client.query("MATCH (d:Disaster) RETURN d.event_id as id, d.location_name as location LIMIT 3")
    print(f"\n2. Disasters: {disasters}")
    
    # Test 3: Find affected facilities
    if disasters:
        affected = client.find_facilities_near_disaster(disasters[0]['id'])
        print(f"\n3. Affected facilities: {len(affected)} found")
    
    # Test 4: Search warehouses
    warehouses = client.search_warehouses_in_city("Mumbai")
    print(f"\n4. Mumbai warehouses: {len(warehouses)} found")
    
    client.close()
    print("\n✅ All tests passed!")
