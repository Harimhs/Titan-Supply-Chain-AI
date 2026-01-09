"""
Load TITAN data into Neo4j - UPDATED FOR NEW SCHEMA
"""

import os
import json
import pandas as pd
import geopandas as gpd
from neo4j import GraphDatabase
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# --- CONFIG ---
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "June#12345")
BATCH_SIZE = 5000
DATA_DIR = Path(__file__).parent.parent / "data"


class TitanLoader:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        self.verify_connection()

    def verify_connection(self):
        try:
            self.driver.verify_connectivity()
            print("✅ Connected to Neo4j")
        except Exception as e:
            print(f"❌ Connection Failed: {e}")
            print("\n💡 Make sure Neo4j is running:")
            print("   docker ps | grep neo4j")
            raise

    def close(self):
        self.driver.close()

    def clear_database(self):
        """Delete all existing data"""
        print("🗑️  Clearing existing data...")
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("   ✅ Database cleared")

    def create_constraints(self):
        print("🛡️  Creating constraints and indexes...")
        queries = [
            # Unique constraints (NEW SCHEMA: using 'id' field)
            "CREATE CONSTRAINT factory_id IF NOT EXISTS FOR (f:Factory) REQUIRE f.id IS UNIQUE",
            "CREATE CONSTRAINT port_id IF NOT EXISTS FOR (p:Port) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT warehouse_id IF NOT EXISTS FOR (w:Warehouse) REQUIRE w.id IS UNIQUE",
            "CREATE CONSTRAINT product_sku IF NOT EXISTS FOR (p:Product) REQUIRE p.sku IS UNIQUE",
            "CREATE CONSTRAINT disaster_id IF NOT EXISTS FOR (d:Disaster) REQUIRE d.id IS UNIQUE",
            
            # Spatial indexes for each node type
            "CREATE INDEX factory_location IF NOT EXISTS FOR (f:Factory) ON (f.lat, f.lon)",
            "CREATE INDEX port_location IF NOT EXISTS FOR (p:Port) ON (p.lat, p.lon)",
            "CREATE INDEX warehouse_location IF NOT EXISTS FOR (w:Warehouse) ON (w.lat, w.lon)",
            "CREATE INDEX disaster_location IF NOT EXISTS FOR (d:Disaster) ON (d.lat, d.lon)",
            
            # Additional indexes
            "CREATE INDEX product_category IF NOT EXISTS FOR (p:Product) ON (p.category)",
            "CREATE INDEX factory_industry IF NOT EXISTS FOR (f:Factory) ON (f.industry)",
            "CREATE INDEX warehouse_type IF NOT EXISTS FOR (w:Warehouse) ON (w.type)",
        ]
        
        with self.driver.session() as session:
            for q in queries:
                try:
                    session.run(q)
                    print(f"   ✅ {q.split()[1]}")
                except Exception as e:
                    print(f"   ⚠️  {e}")

    def load_nodes_from_geojson(self, file_path, label):
        """Load nodes from GeoJSON (NEW: uses 'id' field)"""
        print(f"📦 Loading {label} nodes from {file_path.name}...")
        
        if not file_path.exists():
            print(f"   ⚠️  File not found: {file_path}")
            return
        
        gdf = gpd.read_file(file_path)
        
        # Convert to list of dicts
        records = []
        for _, row in gdf.iterrows():
            props = row.drop('geometry').to_dict()
            props = {k: (v if pd.notna(v) else None) for k, v in props.items()}
            props['lat'] = row.geometry.y
            props['lon'] = row.geometry.x
            records.append(props)
        
        # Use 'id' field (NEW SCHEMA)
        query = f"""
        UNWIND $batch AS row
        MERGE (n:{label} {{id: row.id}})
        SET n += row,
            n.location = point({{latitude: row.lat, longitude: row.lon}})
        """
        
        self._execute_batch(query, records)

    def load_products(self):
        """Load products (NEW SCHEMA: no subcategory, hs_code, etc.)"""
        path = DATA_DIR / "raw" / "products.csv"
        print(f"📦 Loading Products from {path.name}...")
        
        if not path.exists():
            print(f"   ⚠️  File not found: {path}")
            return
        
        df = pd.read_csv(path)
        records = df.to_dict('records')
        
        query = """
        UNWIND $batch AS row
        MERGE (p:Product {sku: row.sku})
        SET p.name = row.name,
            p.category = row.category,
            p.weight_kg = row.weight_kg,
            p.price_usd = row.price_usd,
            p.manufacturer = row.manufacturer,
            p.lead_time_days = row.lead_time_days
        """
        
        self._execute_batch(query, records)

    def load_routes(self):
        """Load routes from Parquet (NEW: source_id/target_id, not from_id/to_id)"""
        path = DATA_DIR / "processed" / "routes.parquet"
        print(f"🛣️  Loading Routes from {path.name}...")
        
        if not path.exists():
            print(f"   ⚠️  File not found: {path}")
            return
        
        df = pd.read_parquet(path)
        records = df.to_dict('records')
        
        # Factory → Port
        print("   → Creating Factory → Port routes...")
        factory_port = [r for r in records if r['source_type'] == 'factory' and r['target_type'] == 'port']
        if factory_port:
            query = """
            UNWIND $batch AS row
            MATCH (source:Factory {id: row.source_id})
            MATCH (target:Port {id: row.target_id})
            MERGE (source)-[r:SUPPLIES_TO]->(target)
            SET r.distance_km = row.distance_km,
                r.mode = row.transport_mode,
                r.time_days = row.avg_time_days,
                r.cost_per_ton_usd = row.cost_per_ton_usd,
                r.reliability = row.reliability
            """
            self._execute_batch(query, factory_port)
        
        # Port → Port
        print("   → Creating Port → Port routes...")
        port_port = [r for r in records if r['source_type'] == 'port' and r['target_type'] == 'port']
        if port_port:
            query = """
            UNWIND $batch AS row
            MATCH (source:Port {id: row.source_id})
            MATCH (target:Port {id: row.target_id})
            MERGE (source)-[r:SUPPLIES_TO]->(target)
            SET r.distance_km = row.distance_km,
                r.mode = row.transport_mode,
                r.time_days = row.avg_time_days,
                r.cost_per_ton_usd = row.cost_per_ton_usd,
                r.reliability = row.reliability
            """
            self._execute_batch(query, port_port)
        
        # Port → Warehouse
        print("   → Creating Port → Warehouse routes...")
        port_warehouse = [r for r in records if r['source_type'] == 'port' and r['target_type'] == 'warehouse']
        if port_warehouse:
            query = """
            UNWIND $batch AS row
            MATCH (source:Port {id: row.source_id})
            MATCH (target:Warehouse {id: row.target_id})
            MERGE (source)-[r:SUPPLIES_TO]->(target)
            SET r.distance_km = row.distance_km,
                r.mode = row.transport_mode,
                r.time_days = row.avg_time_days,
                r.cost_per_ton_usd = row.cost_per_ton_usd,
                r.reliability = row.reliability
            """
            self._execute_batch(query, port_warehouse)
        
        # Warehouse → Warehouse
        print("   → Creating Warehouse → Warehouse routes...")
        wh_wh = [r for r in records if r['source_type'] == 'warehouse' and r['target_type'] == 'warehouse']
        if wh_wh:
            query = """
            UNWIND $batch AS row
            MATCH (source:Warehouse {id: row.source_id})
            MATCH (target:Warehouse {id: row.target_id})
            MERGE (source)-[r:SUPPLIES_TO]->(target)
            SET r.distance_km = row.distance_km,
                r.mode = row.transport_mode,
                r.time_days = row.avg_time_days,
                r.cost_per_ton_usd = row.cost_per_ton_usd,
                r.reliability = row.reliability
            """
            self._execute_batch(query, wh_wh)

    def load_inventory(self):
        """Load inventory (NEW: product_sku, current_stock, not sku/quantity)"""
        path = DATA_DIR / "processed" / "inventory_snapshot.parquet"
        print(f"📊 Loading Inventory from {path.name}...")
        
        if not path.exists():
            print(f"   ⚠️  File not found: {path}")
            return
        
        df = pd.read_parquet(path)
        records = df.to_dict('records')
        
        query = """
        UNWIND $batch AS row
        MATCH (p:Product {sku: row.product_sku})
        MATCH (w:Warehouse {id: row.warehouse_id})
        MERGE (w)-[r:STOCKS]->(p)
        SET r.current_stock = row.current_stock,
            r.daily_demand = row.daily_demand,
            r.safety_stock = row.safety_stock,
            r.reorder_point = row.reorder_point,
            r.stockout_risk = row.stockout_risk,
            r.days_remaining = row.days_remaining,
            r.last_replenishment = row.last_replenishment
        """
        
        self._execute_batch(query, records)

    def load_disasters(self):
        """Load disasters (NEW: id, start_date, duration_days)"""
        path = DATA_DIR / "raw" / "disasters.json"
        print(f"🔥 Loading Disasters from {path.name}...")
        
        if not path.exists():
            print(f"   ⚠️  File not found: {path}")
            return
        
        with open(path) as f:
            data = json.load(f)
        
        query = """
        UNWIND $batch AS row
        MERGE (d:Disaster {id: row.id})
        SET d.name = row.name,
            d.type = row.type,
            d.severity = row.severity,
            d.location_name = row.location,
            d.lat = row.lat,
            d.lon = row.lon,
            d.location = point({latitude: row.lat, longitude: row.lon}),
            d.start_date = row.start_date,
            d.duration_days = row.duration_days,
            d.affected_radius_km = row.affected_radius_km,
            d.estimated_loss_inr_cr = row.estimated_loss_inr_cr
        """
        
        self._execute_batch(query, data)
        
        # Link disasters to nearby facilities
        print("   → Linking Disasters to nearby facilities...")
        link_query = """
        MATCH (d:Disaster)
        MATCH (n) WHERE (n:Factory OR n:Port OR n:Warehouse)
            AND n.location IS NOT NULL
            AND point.distance(d.location, n.location) < (d.affected_radius_km * 1000)
        MERGE (d)-[:AFFECTS]->(n)
        """
        
        with self.driver.session() as session:
            session.run(link_query)
            print("   ✅ Created disaster-facility relationships")

    def _execute_batch(self, query, data):
        """Execute query in batches"""
        total = len(data)
        if total == 0:
            print("   ⚠️  No data to load")
            return
        
        with self.driver.session() as session:
            for i in range(0, total, BATCH_SIZE):
                batch = data[i:i+BATCH_SIZE]
                try:
                    session.run(query, batch=batch)
                    print(f"   Processed {min(i+BATCH_SIZE, total):,}/{total:,}", end='\r')
                except Exception as e:
                    print(f"\n   ❌ Error in batch {i}: {e}")
                    if i == 0 and batch:
                        print(f"   Sample record: {batch[0]}")
                    raise
        print("")  # New line after progress

    def show_stats(self):
        """Show database statistics"""
        print("\n📊 Database Statistics:")
        with self.driver.session() as session:
            # Node counts
            result = session.run("MATCH (n) RETURN labels(n)[0] as Type, count(n) as Count ORDER BY Count DESC")
            print("\n   Node Counts:")
            for record in result:
                print(f"   {record['Type']:<15} : {record['Count']:>10,}")
            
            # Relationship counts
            result = session.run("MATCH ()-[r]->() RETURN type(r) as Type, count(r) as Count ORDER BY Count DESC")
            print("\n   Relationship Counts:")
            for record in result:
                print(f"   {record['Type']:<15} : {record['Count']:>10,}")


def main():
    loader = TitanLoader()
    
    try:
        # Clear old data
        loader.clear_database()
        
        # Create schema
        loader.create_constraints()
        
        # Load nodes
        print("\n" + "="*70)
        print("STEP 1: LOADING NODES")
        print("="*70)
        loader.load_nodes_from_geojson(DATA_DIR / "raw" / "factories.geojson", "Factory")
        loader.load_nodes_from_geojson(DATA_DIR / "raw" / "ports.geojson", "Port")
        loader.load_nodes_from_geojson(DATA_DIR / "raw" / "warehouses.geojson", "Warehouse")
        loader.load_products()
        
        # Load relationships
        print("\n" + "="*70)
        print("STEP 2: LOADING RELATIONSHIPS")
        print("="*70)
        loader.load_routes()
        loader.load_inventory()
        
        # Load events
        print("\n" + "="*70)
        print("STEP 3: LOADING EVENTS")
        print("="*70)
        loader.load_disasters()
        
        # Show results
        print("\n" + "="*70)
        print("✅ DATA LOADING COMPLETE!")
        print("="*70)
        loader.show_stats()
        
        print("\n🌐 Access Neo4j Browser:")
        print("   URL: http://localhost:7474")
        print("   Username: neo4j")
        print("   Password: June#12345")
        
        print("\n🔍 Try these queries:")
        print("   1. View sample factories:")
        print("      MATCH (f:Factory) RETURN f LIMIT 25")
        print("\n   2. View supply chain path:")
        print("      MATCH path = (f:Factory)-[:SUPPLIES_TO*1..3]->(w:Warehouse)")
        print("      RETURN path LIMIT 5")
        print("\n   3. View disaster impacts:")
        print("      MATCH (d:Disaster)-[:AFFECTS]->(n)")
        print("      RETURN d.name, d.type, count(n) as affected_facilities")
        
    finally:
        loader.close()


if __name__ == "__main__":
    main()
