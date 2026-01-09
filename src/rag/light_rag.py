"""
LightRAG: Fast, minimal RAG for simple factual queries
Uses local caching and optimized retrieval
No heavy graph traversal or web search - just direct lookups
"""

from typing import List, Dict, Optional
from src.graph.neo4j_client import Neo4jClient
from datetime import datetime, timedelta

class LightRAG:
    def __init__(self):
        """
        Initialize lightweight RAG
        Optimized for simple queries that need fast responses
        """
        self.neo4j = Neo4jClient()
        
        # Simple in-memory cache
        self.cache = {}
        self.cache_ttl = timedelta(minutes=5)
        
        print("✅ LightRAG Initialized")
    
    def _get_cache_key(self, query: str) -> str:
        """Generate cache key from query"""
        return query.lower().strip()
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Check if cache entry is still valid"""
        if not cache_entry:
            return False
        
        cached_time = cache_entry.get('timestamp')
        if not cached_time:
            return False
        
        age = datetime.now() - cached_time
        return age < self.cache_ttl
    
    def _get_from_cache(self, query: str) -> Optional[Dict]:
        """Retrieve from cache if valid"""
        key = self._get_cache_key(query)
        entry = self.cache.get(key)
        
        if entry and self._is_cache_valid(entry):
            print(f"💾 Cache hit: {key[:50]}...")
            return entry['data']
        
        return None
    
    def _save_to_cache(self, query: str, data: Dict):
        """Save to cache with timestamp"""
        key = self._get_cache_key(query)
        self.cache[key] = {
            'data': data,
            'timestamp': datetime.now()
        }
    
    def quick_product_lookup(self, product_name: str) -> Dict:
        """
        Fast product lookup by name/SKU
        
        Args:
            product_name: Product name or SKU
        
        Returns:
            Product details
        """
        # Check cache
        cached = self._get_from_cache(f"product:{product_name}")
        if cached:
            return cached
        
        # Query Neo4j
        results = self.neo4j.query("""
            MATCH (p:Product)
            WHERE p.name CONTAINS $name OR p.sku CONTAINS $name
            RETURN p.sku as sku,
                   p.name as name,
                   p.category as category,
                   p.value_usd as value,
                   p.weight_kg as weight
            LIMIT 5
        """, {"name": product_name})
        
        data = {'products': results, 'query': product_name}
        self._save_to_cache(f"product:{product_name}", data)
        
        return data
    
    def quick_facility_lookup(self, city: str) -> Dict:
        """
        Fast facility lookup by city
        
        Args:
            city: City name
        
        Returns:
            List of facilities in city
        """
        # Check cache
        cached = self._get_from_cache(f"city:{city}")
        if cached:
            return cached
        
        # Query Neo4j
        results = self.neo4j.query("""
            MATCH (n)
            WHERE (n:Factory OR n:Port OR n:Warehouse)
              AND n.city CONTAINS $city
            RETURN labels(n)[0] as type,
                   coalesce(n.name, n.factory_id, n.port_id, n.warehouse_id) as id,
                   n.city as city,
                   n.country as country
            LIMIT 20
        """, {"city": city})
        
        data = {'facilities': results, 'city': city, 'count': len(results)}
        self._save_to_cache(f"city:{city}", data)
        
        return data
    
    def quick_inventory_check(self, sku: str, location: str = None) -> Dict:
        """
        Fast inventory availability check
        
        Args:
            sku: Product SKU
            location: Optional location filter
        
        Returns:
            Inventory locations and quantities
        """
        cache_key = f"inventory:{sku}:{location or 'all'}"
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        if location:
            query = """
                MATCH (w:Warehouse)-[r:STOCKS]->(p:Product {sku: $sku})
                WHERE w.city CONTAINS $location OR w.country CONTAINS $location
                RETURN w.warehouse_id as warehouse,
                       w.city as city,
                       w.country as country,
                       r.quantity as quantity
                ORDER BY r.quantity DESC
                LIMIT 10
            """
            params = {"sku": sku, "location": location}
        else:
            query = """
                MATCH (w:Warehouse)-[r:STOCKS]->(p:Product {sku: $sku})
                RETURN w.warehouse_id as warehouse,
                       w.city as city,
                       w.country as country,
                       r.quantity as quantity
                ORDER BY r.quantity DESC
                LIMIT 10
            """
            params = {"sku": sku}
        
        results = self.neo4j.query(query, params)
        
        data = {
            'sku': sku,
            'location_filter': location,
            'warehouses': results,
            'total_locations': len(results)
        }
        
        self._save_to_cache(cache_key, data)
        return data
    
    def quick_stats(self) -> Dict:
        """
        Get quick supply chain statistics
        Heavily cached
        """
        cached = self._get_from_cache("stats:global")
        if cached:
            return cached
        
        stats = self.neo4j.get_supply_chain_stats()
        
        self._save_to_cache("stats:global", stats)
        return stats
    
    def get_context_for_query(self, query: str, max_tokens: int = 1500) -> str:
        """
        Get lightweight context for simple queries
        
        Args:
            query: User query
            max_tokens: Token budget
        
        Returns:
            Formatted context string
        """
        context = "### LightRAG Context (Fast Lookup)\n\n"
        
        query_lower = query.lower()
        
        # Route to appropriate quick lookup
        if 'product' in query_lower or 'sku' in query_lower:
            # Extract product name (simplified)
            words = query_lower.split()
            product_name = words[-1]  # Last word as product hint
            
            data = self.quick_product_lookup(product_name)
            if data['products']:
                context += "**Products Found:**\n"
                for p in data['products'][:3]:
                    context += f"- {p['name']} ({p['sku']}): ${p['value']} USD\n"
                context += "\n"
        
        elif 'city' in query_lower or 'warehouse' in query_lower or 'factory' in query_lower:
            # Extract city name
            city_keywords = ['mumbai', 'shanghai', 'beijing', 'delhi', 'singapore', 'tokyo']
            city = next((c for c in city_keywords if c in query_lower), None)
            
            if city:
                data = self.quick_facility_lookup(city)
                context += f"**Facilities in {city.title()}:**\n"
                context += f"- Total found: {data['count']}\n"
                
                # Group by type
                types = {}
                for f in data['facilities']:
                    t = f['type']
                    types[t] = types.get(t, 0) + 1
                
                for ftype, count in types.items():
                    context += f"- {ftype}: {count}\n"
                context += "\n"
        
        elif 'inventory' in query_lower or 'stock' in query_lower:
            context += "**Note:** Use VectorRAG for detailed inventory queries.\n\n"
        
        else:
            # General stats
            stats = self.quick_stats()
            context += "**Supply Chain Overview:**\n"
            for node_type, count in stats.get('nodes', {}).items():
                context += f"- {node_type}: {count:,}\n"
            context += "\n"
        
        # Truncate
        max_chars = max_tokens * 4
        if len(context) > max_chars:
            context = context[:max_chars] + "...\n[Truncated]"
        
        return context
    
    def close(self):
        """Close connections"""
        self.neo4j.close()


# Quick test
if __name__ == "__main__":
    print("🧪 Testing LightRAG...")
    
    light_rag = LightRAG()
    
    try:
        # Test 1: Product lookup
        print("\n📦 Test 1: Product Lookup")
        result = light_rag.quick_product_lookup("phone")
        print(f"Found {len(result['products'])} products")
        for p in result['products'][:3]:
            print(f"  - {p['name']} ({p['sku']})")
        
        # Test 2: Facility lookup (with cache test)
        print("\n🏭 Test 2: Facility Lookup (Mumbai)")
        result1 = light_rag.quick_facility_lookup("Mumbai")
        print(f"First call: {result1['count']} facilities")
        
        result2 = light_rag.quick_facility_lookup("Mumbai")
        print(f"Second call (cached): {result2['count']} facilities")
        
        # Test 3: Stats
        print("\n📊 Test 3: Quick Stats")
        stats = light_rag.quick_stats()
        print(f"Nodes: {stats['nodes']}")
        
        # Test 4: Context generation
        print("\n📄 Test 4: Context Generation")
        context = light_rag.get_context_for_query("Show facilities in Shanghai", max_tokens=500)
        print(context[:300] + "...")
        
    finally:
        light_rag.close()
    
    print("\n✅ LightRAG Tests Complete!")
