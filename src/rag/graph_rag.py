"""
GraphRAG: Supply chain path analysis using Neo4j
Handles complex multi-hop queries and cascade analysis
"""

from src.graph.neo4j_client import Neo4jClient
from typing import List, Dict, Optional
import json

class GraphRAG:
    def __init__(self):
        """Initialize Neo4j client"""
        self.neo4j = Neo4jClient()
        print("✅ GraphRAG Initialized")

    def get_active_disasters(self) -> List[Dict]:
        """Get all active disasters from Neo4j"""
        disasters = self.neo4j.query("""
            MATCH (d:Disaster) 
            RETURN d.disaster_id as id,
                d.event_id as event_id,
                d.location_name as location_name,
                d.type as type,
                d.severity as severity,
                d.recovery_days as recovery_days
            LIMIT 10
        """)
        return disasters if disasters else []

    def generate_context(self, query: str) -> str:
        """Alias for get_context_for_query"""
        return self.get_context_for_query(query, max_tokens=3000)

    
    def get_active_disasters(self) -> List[Dict]:
        """
        Get all active disasters from Neo4j
        Used by orchestrator
        """
        disasters = self.neo4j.query("""
            MATCH (d:Disaster) 
            RETURN coalesce(d.disaster_id, d.event_id) as id,
                d.event_id as event_id,
                d.location_name as location_name,
                d.type as type,
                coalesce(d.severity, 'Unknown') as severity,
                coalesce(d.recovery_days, 0) as recovery_days,
                d.lat as lat,
                d.lon as lon
            ORDER BY d.date DESC
            LIMIT 10
        """)
        return disasters if disasters else []

    
    def generate_context(self, query: str) -> str:
        """Alias for get_context_for_query (for orchestrator compatibility)"""
        return self.get_context_for_query(query, max_tokens=3000)

    def analyze_ripple_effect(self, disaster_id: str, max_hops: int = 5) -> Dict:
        """
        Analyze cascade impact from a disaster
        
        Returns:
            {
                'directly_affected': [...],
                'cascade': {...},
                'total_facilities_at_risk': int
            }
        """
        # Get directly affected facilities
        directly_affected = self.neo4j.find_facilities_near_disaster(disaster_id)
        
        # Get downstream cascade
        cascade = {}
        for tier in range(1, max_hops + 1):
            cascade[f'tier_{tier}'] = []
        
        # For each affected facility, find downstream impacts
        for facility in directly_affected[:10]:  # Limit to prevent explosion
            facility_id = facility['facility_id']
            
            # Try different ID fields based on facility type
            id_field = None
            if facility['facility_type'] == 'Factory':
                id_field = 'factory_id'
            elif facility['facility_type'] == 'Port':
                id_field = 'port_id'
            elif facility['facility_type'] == 'Warehouse':
                id_field = 'warehouse_id'
            
            if not id_field:
                continue
            
            downstream = self.neo4j.query(f"""
                MATCH (victim {{{id_field}: $fid}})
                MATCH path = (victim)-[:SUPPLIES_TO*1..{max_hops}]->(downstream)
                RETURN distinct downstream, length(path) as tier
                LIMIT 50
            """, {"fid": facility_id})
            
            for item in downstream:
                tier = item['tier']
                if tier <= max_hops:
                    cascade[f'tier_{tier}'].append(item['downstream'])
        
        return {
            'directly_affected': directly_affected,
            'cascade': cascade,
            'total_facilities_at_risk': len(directly_affected) + sum(len(v) for v in cascade.values())
        }
    
    def find_supply_chain_path(self, start_location: str, end_location: str) -> Dict:
        """
        Find supply chain path between two locations
        
        Args:
            start_location: City/country name
            end_location: City/country name
        
        Returns:
            {
                'path_found': bool,
                'hops': int,
                'nodes': [...]
            }
        """
        # Find nodes matching locations
        start_nodes = self.neo4j.query("""
            MATCH (n)
            WHERE n.city CONTAINS $loc OR n.country CONTAINS $loc
            RETURN n LIMIT 5
        """, {"loc": start_location})
        
        end_nodes = self.neo4j.query("""
            MATCH (n)
            WHERE n.city CONTAINS $loc OR n.country CONTAINS $loc
            RETURN n LIMIT 5
        """, {"loc": end_location})
        
        if not start_nodes or not end_nodes:
            return {'path_found': False, 'error': 'Locations not found'}
        
        # Find shortest path
        start_id = list(start_nodes[0]['n'].values())[0]  # Get first ID field
        end_id = list(end_nodes[0]['n'].values())[0]
        
        path_result = self.neo4j.trace_supply_chain(start_id, end_id, max_hops=6)
        
        if path_result:
            return {
                'path_found': True,
                'hops': path_result[0]['hops'],
                'node_types': path_result[0]['node_types'],
                'node_names': path_result[0]['node_names']
            }
        else:
            return {'path_found': False, 'error': 'No path exists'}
    
    def find_alternative_suppliers(self, product_sku: str, affected_warehouse_id: str) -> List[Dict]:
        """
        Find alternative warehouses stocking the same product
        Critical for disaster recovery
        """
        results = self.neo4j.query("""
            MATCH (w:Warehouse)-[r:STOCKS]->(p:Product {sku: $sku})
            WHERE w.warehouse_id <> $affected_id
            RETURN w.warehouse_id as id,
                   w.city as city,
                   w.country as country,
                   r.quantity as quantity
            ORDER BY r.quantity DESC
            LIMIT 10
        """, {"sku": product_sku, "affected_id": affected_warehouse_id})
        
        return results
    
    def get_critical_chokepoints(self) -> List[Dict]:
        """
        Find nodes with highest betweenness centrality
        (Single points of failure in supply chain)
        
        FIX: Uses COUNT {} instead of deprecated size()
        """
        results = self.neo4j.query("""
            MATCH (n)
            WHERE (n:Factory OR n:Port OR n:Warehouse)
            OPTIONAL MATCH (n)-[:SUPPLIES_TO]->(out)
            WITH n, COUNT(out) as outgoing
            OPTIONAL MATCH (n)<-[:SUPPLIES_TO]-(inc)
            WITH n, outgoing, COUNT(inc) as incoming
            WHERE outgoing > 5 OR incoming > 5
            RETURN labels(n)[0] as type,
                   coalesce(n.name, n.factory_id, n.port_id, n.warehouse_id) as id,
                   n.city as city,
                   outgoing,
                   incoming,
                   (outgoing + incoming) as total_connections
            ORDER BY total_connections DESC
            LIMIT 20
        """)
        
        return results
    
    def get_context_for_query(self, query: str, max_tokens: int = 3000) -> str:
        """
        Get formatted graph context for LLM
        Intelligently extracts relevant graph data based on query
        """
        context = "### GraphRAG Context\n\n"
        
        # Detect query type
        query_lower = query.lower()
        
        # ========================================================================
        # DISASTER QUERIES
        # ========================================================================
        if any(word in query_lower for word in ['disaster', 'earthquake', 'typhoon', 'impact', 'affected']):
            disasters = self.neo4j.query("""
                MATCH (d:Disaster) 
                RETURN d.event_id as id, 
                    d.location_name as location, 
                    d.type as type,
                    coalesce(d.severity, 'Unknown') as severity,
                    coalesce(d.recovery_days, 0) as recovery_days
                ORDER BY d.date DESC
                LIMIT 5
            """)
            
            if disasters:
                # ✅ NEW: Find disaster matching query location
                query_disaster = None
                for d in disasters:
                    if d['location'].lower() in query_lower:
                        query_disaster = d
                        break
                
                # Use matched disaster or first one
                target_disaster = query_disaster or disasters[0]
                
                context += "**Active Disasters:**\n"
                for d in disasters:
                    marker = " ⭐" if d == target_disaster else ""
                    context += f"- {d['location']}: {d['type']} (Severity: {d['severity']}, Recovery: {d['recovery_days']} days){marker}\n"
                context += "\n"
                
                # Get impact of matched disaster
                impact = self.analyze_ripple_effect(target_disaster['id'], max_hops=3)
                context += f"**Impact Analysis for {target_disaster['location']}:**\n"
                # ... rest of impact code

                context += f"- Directly affected: {len(impact['directly_affected'])} facilities\n"

                # List specific affected facilities
                if impact['directly_affected']:
                    context += "- Affected facilities:\n"
                    for fac in impact['directly_affected'][:5]:  # Top 5
                        fac_type = fac.get('facility_type') or 'Facility'
                        distance = fac.get('distance_km') or 0
                        context += f"  * {fac_type} at {distance:.1f}km\n"

                context += f"- Total downstream impact: {impact['total_facilities_at_risk']} facilities\n\n"

        
        # ========================================================================
        # WAREHOUSE/PORT/FACTORY COUNT QUERIES
        # ========================================================================
        elif any(word in query_lower for word in ['how many', 'count', 'number of', 'total']):
            # Extract location if mentioned
            location_hints = ['india', 'mumbai', 'china', 'shanghai', 'usa', 'singapore']
            location = next((loc for loc in location_hints if loc in query_lower), None)
            
            if location:
                # Location-specific counts
                context += f"**Facilities in {location.title()}:**\n"
                
                # Factories
                factory_count = self.neo4j.query("""
                    MATCH (f:Factory)
                    WHERE toLower(f.region) CONTAINS $location 
                    OR toLower(f.country) CONTAINS $location
                    RETURN count(f) as count
                """, {"location": location})
                
                # Ports
                port_count = self.neo4j.query("""
                    MATCH (p:Port)
                    WHERE toLower(p.city) CONTAINS $location 
                    OR toLower(p.country) CONTAINS $location
                    RETURN count(p) as count
                """, {"location": location})
                
                # Warehouses
                warehouse_count = self.neo4j.query("""
                    MATCH (w:Warehouse)
                    WHERE toLower(w.city) CONTAINS $location 
                    OR toLower(w.country) CONTAINS $location
                    RETURN count(w) as count
                """, {"location": location})
                
                f_count = factory_count[0]['count'] if factory_count else 0
                p_count = port_count[0]['count'] if port_count else 0
                w_count = warehouse_count[0]['count'] if warehouse_count else 0
                
                context += f"- Factories: {f_count:,}\n"
                context += f"- Ports: {p_count:,}\n"
                context += f"- Warehouses: {w_count:,}\n\n"
            else:
                # Global counts
                stats = self.neo4j.get_supply_chain_stats()
                context += "**Global Supply Chain Statistics:**\n"
                context += f"- Total Factories: {stats['nodes'].get('Factory', 0):,}\n"
                context += f"- Total Ports: {stats['nodes'].get('Port', 0):,}\n"
                context += f"- Total Warehouses: {stats['nodes'].get('Warehouse', 0):,}\n"
                context += f"- Total Products: {stats['nodes'].get('Product', 0):,}\n"
                context += f"- Total Supply Routes: {stats['relationships'].get('SUPPLIES_TO', 0):,}\n\n"
        
        # ========================================================================
        # LOCATION QUERIES (warehouses in X, ports in Y)
        # ========================================================================
        # LOCATION QUERIES (warehouses in X, ports in Y)
        elif any(word in query_lower for word in ['warehouse', 'port', 'factory', 'facility']):
            # Check if location is mentioned
            location_hints = ['india', 'mumbai', 'delhi', 'chennai', 'china', 'shanghai', 'singapore', 'usa', 'europe']
            location = next((loc for loc in location_hints if loc in query_lower), None)
            
            if location and 'warehouse' in query_lower:  # ✅ Add 'warehouse' check
                facilities = self.neo4j.query("""
                    MATCH (w:Warehouse)
                    WHERE toLower(w.city) CONTAINS $location 
                    OR toLower(w.country) CONTAINS $location
                    RETURN w.warehouse_id as id, 
                        w.city as city, 
                        w.type as type,
                        w.capacity_sqft as capacity
                    LIMIT 10
                """, {"location": location})
                
                context += f"**Warehouses in {location.title()}:**\n"
                for w in facilities:
                    city = w.get('city') or 'Unknown'
                    wtype = w.get('type') or 'N/A'
                    capacity = w.get('capacity') or 0
                    context += f"- {w['id']} in {city}, Type: {wtype}, Capacity: {capacity:,} sqft\n"
                
                context += f"\nTotal: Found {len(facilities)} warehouses (showing first 10)\n\n"

                
                # ========================================================================
                # ALTERNATIVE SUPPLIER QUERIES
                # ========================================================================
            elif any(word in query_lower for word in ['alternative', 'backup', 'other', 'different supplier']):
                context += "**Alternative Supply Options:**\n"
                chokepoints = self.get_critical_chokepoints()
                
                if chokepoints:
                    context += "Critical hubs (highest connectivity):\n"
                    for cp in chokepoints[:5]:
                        context += f"- {cp['type']} in {cp.get('city', 'Unknown')}: {cp['total_connections']} connections\n"
                
                context += "\n"
        
        # ========================================================================
        # PATH/ROUTE QUERIES
        # ========================================================================
        elif any(word in query_lower for word in ['path', 'route', 'from', 'to']):
            context += "**Supply Chain Network Statistics:**\n"
            stats = self.neo4j.get_supply_chain_stats()
            context += f"- Total routes: {stats['relationships'].get('SUPPLIES_TO', 0):,}\n"
            context += f"- Factories: {stats['nodes'].get('Factory', 0):,}\n"
            context += f"- Ports: {stats['nodes'].get('Port', 0):,}\n"
            context += f"- Warehouses: {stats['nodes'].get('Warehouse', 0):,}\n\n"
        
        # ========================================================================
        # CRITICAL CHOKEPOINTS
        # ========================================================================
        elif any(word in query_lower for word in ['critical', 'chokepoint', 'important', 'key']):
            context += "**Critical Chokepoints (High-Risk Nodes):**\n"
            chokepoints = self.get_critical_chokepoints()
            for cp in chokepoints[:10]:
                context += f"- {cp['type']} in {cp.get('city', 'Unknown')}: {cp['total_connections']} connections (In: {cp['incoming']}, Out: {cp['outgoing']})\n"
            context += "\n"
        
        # ========================================================================
        # DEFAULT: GENERAL STATS
        # ========================================================================
        else:
            stats = self.neo4j.get_supply_chain_stats()
            context += "**Supply Chain Overview:**\n"
            context += f"- Factories: {stats['nodes'].get('Factory', 0):,}\n"
            context += f"- Ports: {stats['nodes'].get('Port', 0):,}\n"
            context += f"- Warehouses: {stats['nodes'].get('Warehouse', 0):,}\n"
            context += f"- Products: {stats['nodes'].get('Product', 0):,}\n"
            context += f"- Active Routes: {stats['relationships'].get('SUPPLIES_TO', 0):,}\n\n"
        
        # Truncate to token budget
        max_chars = max_tokens * 4
        if len(context) > max_chars:
            context = context[:max_chars] + "...\n[Context truncated due to token budget]"
        
        return context

    
    def close(self):
        """Close Neo4j connection"""
        self.neo4j.close()


# Quick test
if __name__ == "__main__":
    print("🧪 Testing GraphRAG...")
    
    graph_rag = GraphRAG()
    
    try:
        # Test 1: Get disasters
        print("\n📊 Test 1: Active Disasters")
        disasters = graph_rag.neo4j.query("MATCH (d:Disaster) RETURN d.event_id as id, d.location_name as location")
        for d in disasters:
            print(f"   - {d['location']}: {d['id']}")
        
        # Test 2: Ripple effect analysis
        if disasters:
            print(f"\n🌊 Test 2: Ripple Effect Analysis for {disasters[0]['location']}")
            impact = graph_rag.analyze_ripple_effect(disasters[0]['id'], max_hops=3)
            print(f"   Directly affected: {len(impact['directly_affected'])} facilities")
            print(f"   Total at risk: {impact['total_facilities_at_risk']} facilities")
        
        # Test 3: Chokepoints
        print("\n🎯 Test 3: Critical Chokepoints")
        chokepoints = graph_rag.get_critical_chokepoints()
        for cp in chokepoints[:5]:
            print(f"   - {cp['type']} in {cp['city']}: {cp['total_connections']} connections")
        
        # Test 4: Context generation
        print("\n📄 Test 4: Context Generation")
        context = graph_rag.get_context_for_query("Taiwan earthquake impact", max_tokens=1000)
        print(context[:400] + "...")
        
    finally:
        graph_rag.close()
    
    print("\n✅ GraphRAG Tests Complete!")
