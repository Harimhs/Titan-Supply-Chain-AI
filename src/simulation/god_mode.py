"""
God Mode: Interactive node manipulation
Disable/enable nodes and recalculate cascades in real-time
"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

class GodMode:
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "June#12345")
        
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.disabled_nodes = set()
    
    def close(self):
        self.driver.close()
    
    def disable_node(self, node_id, reason="Manual disable"):
        """
        Disable a node (factory/port/warehouse)
        Marks it as disabled in Neo4j and tracks locally
        """
        query = """
        MATCH (n {id: $node_id})
        SET n.disabled = true,
            n.disabled_reason = $reason,
            n.disabled_at = datetime()
        RETURN n.name as name, labels(n)[0] as type
        """
        
        with self.driver.session() as session:
            result = session.run(query, node_id=node_id, reason=reason)
            record = result.single()
            
            if record:
                self.disabled_nodes.add(node_id)
                return {
                    'success': True,
                    'node_id': node_id,
                    'name': record['name'],
                    'type': record['type'],
                    'reason': reason
                }
            else:
                return {'success': False, 'error': 'Node not found'}
    
    def enable_node(self, node_id):
        """Re-enable a disabled node"""
        query = """
        MATCH (n {id: $node_id})
        SET n.disabled = false
        REMOVE n.disabled_reason, n.disabled_at
        RETURN n.name as name
        """
        
        with self.driver.session() as session:
            result = session.run(query, node_id=node_id)
            record = result.single()
            
            if record:
                self.disabled_nodes.discard(node_id)
                return {'success': True, 'node_id': node_id, 'name': record['name']}
            else:
                return {'success': False, 'error': 'Node not found'}
    
    def get_cascade_with_disabled(self, source_id, target_id, max_hops=6):
        """
        Find cascade path avoiding disabled nodes
        """
        query = """
        MATCH path = shortestPath(
            (source {id: $source_id})-[:SUPPLIES_TO*1..%d]->(target {id: $target_id})
        )
        WHERE ALL(node in nodes(path) WHERE node.disabled IS NULL OR node.disabled = false)
        RETURN path, length(path) as hops,
               [node in nodes(path) | {
                   id: node.id, 
                   name: node.name, 
                   type: labels(node)[0],
                   disabled: COALESCE(node.disabled, false)
               }] as nodes
        """ % max_hops
        
        with self.driver.session() as session:
            result = session.run(query, source_id=source_id, target_id=target_id)
            record = result.single()
            
            if record:
                return {
                    'found_path': True,
                    'nodes': record['nodes'],
                    'hops': record['hops']
                }
            else:
                return {
                    'found_path': False,
                    'reason': 'No path available (nodes disabled?)'
                }
    
    def get_affected_warehouses_by_disabled_node(self, disabled_node_id, max_hops=4):
        """
        Find all warehouses that lose connection after node disabled
        """
        # SIMPLIFIED QUERY - Find downstream warehouses
        query = """
        MATCH (disabled {id: $disabled_id})-[:SUPPLIES_TO*1..4]->(w:Warehouse)
        RETURN DISTINCT w.id as warehouse_id, 
            w.name as warehouse_name,
            w.city as city,
            w.country as country
        LIMIT 50
        """
        
        with self.driver.session() as session:
            result = session.run(query, disabled_id=disabled_node_id)
            return [dict(record) for record in result]

        
    def simulate_disaster(self, disaster_type, location_lat, location_lon, radius_km):
        """
        Simulate a new disaster and disable all nodes within radius
        """
        query = """
        MATCH (n)
        WHERE (n:Factory OR n:Port OR n:Warehouse)
          AND n.location IS NOT NULL
          AND point.distance(n.location, point({latitude: $lat, longitude: $lon})) < ($radius * 1000)
        SET n.disabled = true,
            n.disabled_reason = $disaster_type,
            n.disabled_at = datetime()
        RETURN n.id as node_id, n.name as name, labels(n)[0] as type
        """
        
        with self.driver.session() as session:
            result = session.run(
                query, 
                lat=location_lat, 
                lon=location_lon, 
                radius=radius_km,
                disaster_type=disaster_type
            )
            affected = [dict(record) for record in result]
            
            for node in affected:
                self.disabled_nodes.add(node['node_id'])
            
            return {
                'affected_count': len(affected),
                'affected_nodes': affected
            }
    
    def get_disabled_nodes(self):
        """Get list of all currently disabled nodes"""
        query = """
        MATCH (n)
        WHERE n.disabled = true
        RETURN n.id as node_id, 
               n.name as name, 
               labels(n)[0] as type,
               n.disabled_reason as reason
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            return [dict(record) for record in result]
    
    def reset_all(self):
        """Re-enable all disabled nodes"""
        query = """
        MATCH (n)
        WHERE n.disabled = true
        SET n.disabled = false
        REMOVE n.disabled_reason, n.disabled_at
        RETURN count(n) as count
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            count = result.single()['count']
            self.disabled_nodes.clear()
            return {'re_enabled': count}
