#!/usr/bin/env python3
"""
Dashboard Data Loader
Loads and caches data from Neo4j for dashboard visualization
"""

from src.graph.neo4j_client import Neo4jClient
import pandas as pd
from typing import Dict, List
import numpy as np


class DashboardDataLoader:
    """Load and prepare data for dashboard visualization"""
    
    def __init__(self):
        """Initialize and load all data"""
        self.neo4j = Neo4jClient()
        
        # Load data
        self.factories = self._load_factories()
        self.ports = self._load_ports()
        self.warehouses = self._load_warehouses()
        self.disasters = self._load_disasters()
        self.routes = self._load_routes()
        
        # Statistics
        self.stats = {
            'factories': len(self.factories),
            'ports': len(self.ports),
            'warehouses': len(self.warehouses),
            'disasters': len(self.disasters),
            'routes': len(self.routes)
        }
    
    def _load_factories(self) -> pd.DataFrame:
        """Load factory data"""
        query = """
        MATCH (f:Factory)
        RETURN f.factory_id as id,
               f.lat as lat,
               f.lon as lon,
               f.region as region,
               f.country as country,
               f.tier as tier
        LIMIT 1000
        """
        data = self.neo4j.query(query)
        df = pd.DataFrame(data)
        
        # Clean nulls
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        df = df.dropna(subset=['lat', 'lon'])
        
        return df
    
    def _load_ports(self) -> pd.DataFrame:
        """Load port data"""
        query = """
        MATCH (p:Port)
        RETURN p.port_id as id,
               p.name as name,
               p.lat as lat,
               p.lon as lon,
               p.city as city,
               p.country as country,
               p.tier as tier,
               p.annual_TEU as teu
        """
        data = self.neo4j.query(query)
        df = pd.DataFrame(data)
        
        # Clean
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        df['teu'] = pd.to_numeric(df['teu'], errors='coerce').fillna(0)
        df = df.dropna(subset=['lat', 'lon'])
        
        return df
    
    def _load_warehouses(self) -> pd.DataFrame:
        """Load warehouse data"""
        query = """
        MATCH (w:Warehouse)
        RETURN w.warehouse_id as id,
               w.lat as lat,
               w.lon as lon,
               w.city as city,
               w.country as country,
               w.type as type
        LIMIT 5000
        """
        data = self.neo4j.query(query)
        df = pd.DataFrame(data)
        
        # Clean
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        df = df.dropna(subset=['lat', 'lon'])
        
        return df
    
    def _load_disasters(self) -> pd.DataFrame:
        """Load active disasters"""
        query = """
        MATCH (d:Disaster)
        RETURN d.disaster_id as id,
               d.event_id as event_id,
               d.location_name as location,
               d.type as type,
               d.lat as lat,
               d.lon as lon,
               d.severity as severity,
               d.radius_km as radius,
               coalesce(d.recovery_days, 0) as recovery_days
        """
        data = self.neo4j.query(query)
        df = pd.DataFrame(data)
        
        if not df.empty:
            df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
            df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
            df['radius'] = pd.to_numeric(df['radius'], errors='coerce').fillna(100)
            df = df.dropna(subset=['lat', 'lon'])
        
        return df
    
    def _load_routes(self) -> List[Dict]:
        """Load supply chain routes (sample for visualization)"""
        query = """
        MATCH (a)-[r:SUPPLIES_TO]->(b)
        WHERE (a:Factory OR a:Port) AND (b:Port OR b:Warehouse)
        AND a.lat IS NOT NULL AND a.lon IS NOT NULL 
        AND b.lat IS NOT NULL AND b.lon IS NOT NULL
        WITH a, b, r
        LIMIT 500
        RETURN a.lat as src_lat,
            a.lon as src_lon,
            b.lat as dst_lat,
            b.lon as dst_lon,
            labels(a)[0] as src_type,
            labels(b)[0] as dst_type
        """
        data = self.neo4j.query(query)
        
        # Clean and validate routes
        routes = []
        for route in data:
            try:
                src_lat = float(route.get('src_lat', 0))
                src_lon = float(route.get('src_lon', 0))
                dst_lat = float(route.get('dst_lat', 0))
                dst_lon = float(route.get('dst_lon', 0))
                
                # Validate coordinates
                if (abs(src_lat) <= 90 and abs(src_lon) <= 180 and 
                    abs(dst_lat) <= 90 and abs(dst_lon) <= 180 and
                    src_lat != 0 and src_lon != 0 and 
                    dst_lat != 0 and dst_lon != 0):
                    routes.append({
                        'src_lat': src_lat,
                        'src_lon': src_lon,
                        'dst_lat': dst_lat,
                        'dst_lon': dst_lon,
                        'src_type': route.get('src_type', 'Unknown'),
                        'dst_type': route.get('dst_type', 'Unknown')
                    })
            except (ValueError, TypeError):
                continue
        
        return routes

    
    def get_facilities_by_region(self, region: str) -> Dict[str, pd.DataFrame]:
        """Get facilities filtered by region"""
        return {
            'factories': self.factories[self.factories['region'].str.contains(region, case=False, na=False)],
            'ports': self.ports[self.ports['country'].str.contains(region, case=False, na=False)],
            'warehouses': self.warehouses[self.warehouses['country'].str.contains(region, case=False, na=False)]
        }
    
    def get_disaster_affected_facilities(self, disaster_id: str) -> pd.DataFrame:
        """Get facilities affected by a specific disaster"""
        query = """
        MATCH (d:Disaster {disaster_id: $disaster_id})-[r:AFFECTS]->(f)
        RETURN f.lat as lat,
               f.lon as lon,
               labels(f)[0] as type,
               r.distance_km as distance
        LIMIT 100
        """
        data = self.neo4j.query(query, {"disaster_id": disaster_id})
        return pd.DataFrame(data)
    
    def close(self):
        """Close Neo4j connection"""
        self.neo4j.close()


# Test
if __name__ == "__main__":
    print("🧪 Testing Data Loader...")
    
    loader = DashboardDataLoader()
    
    print(f"\n✅ Loaded Data:")
    print(f"   Factories: {len(loader.factories):,}")
    print(f"   Ports: {len(loader.ports):,}")
    print(f"   Warehouses: {len(loader.warehouses):,}")
    print(f"   Disasters: {len(loader.disasters):,}")
    print(f"   Routes: {len(loader.routes):,}")
    
    print(f"\n📊 Sample Factory:")
    print(loader.factories.head(1).to_dict('records'))
    
    print(f"\n📊 Sample Port:")
    print(loader.ports.head(1).to_dict('records'))
    
    print(f"\n📊 Sample Disaster:")
    if not loader.disasters.empty:
        print(loader.disasters.head(1).to_dict('records'))
    
    loader.close()
    print("\n✅ Data Loader Tests Complete!")
