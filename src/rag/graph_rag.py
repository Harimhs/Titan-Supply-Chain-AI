"""
GraphRAG: Multi-hop supply chain traversal using Neo4j
"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

class GraphRAG:
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "June#12345")
        
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def get_cascade_path(self, source_id, target_id, max_hops=6):
        """
        Find supply chain path from source to target (e.g., Taiwan TSMC → Coimbatore)
        Returns: List of nodes and relationships
        """
        query = """
        MATCH path = shortestPath(
            (source {id: $source_id})-[:SUPPLIES_TO*1..%d]->(target {id: $target_id})
        )
        RETURN path, length(path) as hops,
               [node in nodes(path) | {
                   id: node.id, 
                   name: node.name, 
                   type: labels(node)[0],
                   city: node.city,
                   country: node.country
               }] as nodes,
               [rel in relationships(path) | {
                   distance_km: rel.distance_km,
                   time_days: rel.time_days,
                   mode: rel.mode
               }] as edges
        """ % max_hops
        
        with self.driver.session() as session:
            result = session.run(query, source_id=source_id, target_id=target_id)
            record = result.single()
            
            if record:
                return {
                    'nodes': record['nodes'],
                    'edges': record['edges'],
                    'hops': record['hops'],
                    'total_time_days': sum(e['time_days'] for e in record['edges'] if e['time_days']),
                    'total_distance_km': sum(e['distance_km'] for e in record['edges'] if e['distance_km'])
                }
            return None
    
    def find_affected_nodes(self, disaster_id, radius_km=None):
        """
        Find all facilities affected by a disaster
        Uses spatial search based on disaster's affected_radius_km
        """
        query = """
        MATCH (d:Disaster {id: $disaster_id})
        MATCH (d)-[:AFFECTS]->(n)
        RETURN n.id as id, n.name as name, labels(n)[0] as type,
               n.city as city, n.country as country,
               point.distance(d.location, n.location) / 1000 as distance_km
        ORDER BY distance_km
        """
        
        with self.driver.session() as session:
            result = session.run(query, disaster_id=disaster_id)
            return [dict(record) for record in result]
    
    def get_downstream_impact(self, facility_id, max_hops=4):
        """
        Find all downstream facilities affected if this facility fails
        (e.g., if Taiwan TSMC fails, what warehouses are impacted?)
        """
        query = """
        MATCH path = (source {id: $facility_id})-[:SUPPLIES_TO*1..%d]->(downstream)
        WHERE downstream:Warehouse
        RETURN DISTINCT downstream.id as id, 
               downstream.name as name,
               downstream.city as city,
               downstream.country as country,
               length(path) as hops,
               min([rel in relationships(path) | rel.time_days]) as min_time_days
        ORDER BY hops, min_time_days
        LIMIT 50
        """ % max_hops
        
        with self.driver.session() as session:
            result = session.run(query, facility_id=facility_id)
            return [dict(record) for record in result]
    
    def get_critical_products_at_warehouse(self, warehouse_id):
        """
        Get products with critical stock levels at a warehouse
        """
        query = """
        MATCH (w:Warehouse {id: $warehouse_id})-[r:STOCKS]->(p:Product)
        WHERE r.stockout_risk IN ['CRITICAL', 'HIGH']
        RETURN p.sku as sku, p.name as name, p.category as category,
               r.current_stock as current_stock,
               r.daily_demand as daily_demand,
               r.days_remaining as days_remaining,
               r.stockout_risk as risk
        ORDER BY r.days_remaining
        """
        
        with self.driver.session() as session:
            result = session.run(query, warehouse_id=warehouse_id)
            return [dict(record) for record in result]
    
    def get_alternate_suppliers(self, product_sku, exclude_factory_ids=[], max_results=5):
        """
        Find alternate factories that can supply a product
        (For rerouting when primary supplier fails)
        """
        query = """
        MATCH (f:Factory)-[:SUPPLIES_TO*1..3]->(w:Warehouse)-[r:STOCKS]->(p:Product {sku: $product_sku})
        WHERE NOT f.id IN $exclude_ids
        RETURN DISTINCT f.id as factory_id, f.name as factory_name, 
               f.city as city, f.country as country,
               f.industry as industry,
               count(DISTINCT w) as warehouse_coverage
        ORDER BY warehouse_coverage DESC
        LIMIT $max_results
        """
        
        with self.driver.session() as session:
            result = session.run(
                query, 
                product_sku=product_sku, 
                exclude_ids=exclude_factory_ids,
                max_results=max_results
            )
            return [dict(record) for record in result]
