#!/usr/bin/env python3
"""
Load all generated CSV data into Neo4j
Updated to match new data generation structure
"""
import sys
from pathlib import Path
import pandas as pd
from neo4j import GraphDatabase
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Neo4j Configuration
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "June#12345"

class Neo4jLoader:
    def __init__(self, uri, user, password):
        """Initialize Neo4j connection"""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.data_dir = project_root / "data" / "processed"
        
    def close(self):
        """Close Neo4j connection"""
        self.driver.close()
    
    def clear_database(self):
        """Clear all existing data"""
        print("🗑️  Clearing existing data...")
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("   ✅ Database cleared\n")
    
    def create_constraints(self):
        """Create constraints and indexes"""
        print("🛡️  Creating constraints and indexes...")
        
        constraints = [
            "CREATE CONSTRAINT factory_id IF NOT EXISTS FOR (f:Factory) REQUIRE f.id IS UNIQUE",
            "CREATE CONSTRAINT port_id IF NOT EXISTS FOR (p:Port) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT warehouse_id IF NOT EXISTS FOR (w:Warehouse) REQUIRE w.id IS UNIQUE",
            "CREATE CONSTRAINT product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT disaster_id IF NOT EXISTS FOR (d:Disaster) REQUIRE d.id IS UNIQUE",
        ]
        
        indexes = [
            "CREATE INDEX factory_country IF NOT EXISTS FOR (f:Factory) ON (f.country)",
            "CREATE INDEX factory_product IF NOT EXISTS FOR (f:Factory) ON (f.product_type)",
            "CREATE INDEX port_country IF NOT EXISTS FOR (p:Port) ON (p.country)",
            "CREATE INDEX warehouse_country IF NOT EXISTS FOR (w:Warehouse) ON (w.country)",
            "CREATE INDEX disaster_type IF NOT EXISTS FOR (d:Disaster) ON (d.type)",
        ]
        
        with self.driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                    print("   ✅ CONSTRAINT")
                except Exception as e:
                    print(f"   ⚠️  Constraint exists or error: {str(e)[:50]}")
            
            for index in indexes:
                try:
                    session.run(index)
                    print("   ✅ INDEX")
                except Exception as e:
                    print(f"   ⚠️  Index exists or error: {str(e)[:50]}")
        
        print()
    
    def load_factories(self):
        """Load Factory nodes from factories.csv"""
        print("🏭 Loading Factories...")
        csv_file = self.data_dir / "factories.csv"
        
        if not csv_file.exists():
            print(f"   ⚠️  File not found: {csv_file}")
            return 0
        
        df = pd.read_csv(csv_file)
        
        with self.driver.session() as session:
            count = 0
            for _, row in df.iterrows():
                session.run("""
                    CREATE (f:Factory {
                        id: $id,
                        name: $name,
                        city: $city,
                        country: $country,
                        lat: $lat,
                        lon: $lon,
                        capacity: $capacity,
                        product_type: $product_type,
                        operational_status: $operational_status
                    })
                """, 
                    id=row['id'],
                    name=row['name'],
                    city=row['city'],
                    country=row['country'],
                    lat=float(row['lat']),
                    lon=float(row['lon']),
                    capacity=int(row['capacity']),
                    product_type=row['product_type'],
                    operational_status=row['operational_status']
                )
                count += 1
            
        print(f"   ✅ Loaded {count} factories\n")
        return count
    
    def load_ports(self):
        """Load Port nodes from ports.csv"""
        print("⚓ Loading Ports...")
        csv_file = self.data_dir / "ports.csv"
        
        if not csv_file.exists():
            print(f"   ⚠️  File not found: {csv_file}")
            return 0
        
        df = pd.read_csv(csv_file)
        
        with self.driver.session() as session:
            count = 0
            for _, row in df.iterrows():
                session.run("""
                    CREATE (p:Port {
                        id: $id,
                        name: $name,
                        city: $city,
                        country: $country,
                        lat: $lat,
                        lon: $lon,
                        capacity: $capacity,
                        port_type: $port_type
                    })
                """,
                    id=row['id'],
                    name=row['name'],
                    city=row['city'],
                    country=row['country'],
                    lat=float(row['lat']),
                    lon=float(row['lon']),
                    capacity=int(row['capacity']),
                    port_type=row['port_type']
                )
                count += 1
        
        print(f"   ✅ Loaded {count} ports\n")
        return count
    
    def load_warehouses(self):
        """Load Warehouse nodes from warehouses.csv"""
        print("🏢 Loading Warehouses...")
        csv_file = self.data_dir / "warehouses.csv"
        
        if not csv_file.exists():
            print(f"   ⚠️  File not found: {csv_file}")
            return 0
        
        df = pd.read_csv(csv_file)
        
        with self.driver.session() as session:
            count = 0
            for _, row in df.iterrows():
                session.run("""
                    CREATE (w:Warehouse {
                        id: $id,
                        name: $name,
                        city: $city,
                        country: $country,
                        lat: $lat,
                        lon: $lon,
                        capacity: $capacity,
                        warehouse_type: $warehouse_type
                    })
                """,
                    id=row['id'],
                    name=row['name'],
                    city=row['city'],
                    country=row['country'],
                    lat=float(row['lat']),
                    lon=float(row['lon']),
                    capacity=int(row['capacity']),
                    warehouse_type=row['warehouse_type']
                )
                count += 1
        
        print(f"   ✅ Loaded {count} warehouses\n")
        return count
    
    def load_products(self):
        """Load Product nodes from products.csv"""
        print("📦 Loading Products...")
        csv_file = self.data_dir / "products.csv"
        
        if not csv_file.exists():
            print(f"   ⚠️  File not found: {csv_file}")
            return 0
        
        df = pd.read_csv(csv_file)
        
        with self.driver.session() as session:
            count = 0
            for _, row in df.iterrows():
                session.run("""
                    CREATE (p:Product {
                        id: $id,
                        name: $name,
                        description: $description,
                        category: $category,
                        avg_price: $avg_price,
                        weight_kg: $weight_kg
                    })
                """,
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    category=row['category'],
                    avg_price=float(row['avg_price']),
                    weight_kg=float(row['weight_kg'])
                )
                count += 1
        
        print(f"   ✅ Loaded {count} products\n")
        return count
    
    def load_disasters(self):
        """Load Disaster nodes from disasters.csv"""
        print("🌪️  Loading Disasters...")
        csv_file = self.data_dir / "disasters.csv"
        
        if not csv_file.exists():
            print(f"   ⚠️  File not found: {csv_file}")
            return 0
        
        df = pd.read_csv(csv_file)
        
        with self.driver.session() as session:
            count = 0
            for _, row in df.iterrows():
                session.run("""
                    CREATE (d:Disaster {
                        id: $id,
                        type: $type,
                        severity: $severity,
                        lat: $lat,
                        lon: $lon,
                        city: $city,
                        country: $country,
                        impact_radius_km: $impact_radius_km,
                        affected_entities: $affected_entities,
                        affected_count: $affected_count,
                        start_date: $start_date,
                        status: $status,
                        description: $description
                    })
                """,
                    id=row['id'],
                    type=row['type'],
                    severity=row['severity'],
                    lat=float(row['lat']),
                    lon=float(row['lon']),
                    city=row['city'],
                    country=row['country'],
                    impact_radius_km=float(row['impact_radius_km']),
                    affected_entities=row['affected_entities'],
                    affected_count=int(row['affected_count']),
                    start_date=row['start_date'],
                    status=row['status'],
                    description=row['description']
                )
                count += 1
        
        print(f"   ✅ Loaded {count} disasters\n")
        return count
    
    def load_supply_relationships(self):
        """Load SUPPLIES_TO relationships from supply_relationships.csv"""
        print("🔗 Loading SUPPLIES_TO relationships...")
        csv_file = self.data_dir / "supply_relationships.csv"
        
        if not csv_file.exists():
            print(f"   ⚠️  File not found: {csv_file}")
            return 0
        
        df = pd.read_csv(csv_file)
        
        with self.driver.session() as session:
            count = 0
            for _, row in df.iterrows():
                # Match source and target by type
                query = f"""
                    MATCH (source:{row['source_type']} {{id: $source_id}})
                    MATCH (target:{row['target_type']} {{id: $target_id}})
                    CREATE (source)-[r:SUPPLIES_TO {{
                        id: $rel_id,
                        product_id: $product_id,
                        quantity: $quantity,
                        frequency: $frequency,
                        distance_km: $distance_km
                    }}]->(target)
                """
                
                session.run(query,
                    source_id=row['source_id'],
                    target_id=row['target_id'],
                    rel_id=row['id'],
                    product_id=row['product_id'],
                    quantity=int(row['quantity']),
                    frequency=row['frequency'],
                    distance_km=float(row['distance_km'])
                )
                count += 1
        
        print(f"   ✅ Loaded {count} SUPPLIES_TO relationships\n")
        return count
    
    def load_stock_relationships(self):
        """Load STOCKS relationships from stock_relationships.csv"""
        print("📊 Loading STOCKS relationships...")
        csv_file = self.data_dir / "stock_relationships.csv"
        
        if not csv_file.exists():
            print(f"   ⚠️  File not found: {csv_file}")
            return 0
        
        df = pd.read_csv(csv_file)
        
        with self.driver.session() as session:
            count = 0
            for _, row in df.iterrows():
                session.run("""
                    MATCH (w:Warehouse {id: $warehouse_id})
                    MATCH (p:Product {id: $product_id})
                    CREATE (w)-[r:STOCKS {
                        id: $stock_id,
                        quantity: $quantity,
                        last_updated: $last_updated
                    }]->(p)
                """,
                    warehouse_id=row['warehouse_id'],
                    product_id=row['product_id'],
                    stock_id=row['id'],
                    quantity=int(row['quantity']),
                    last_updated=row['last_updated']
                )
                count += 1
        
        print(f"   ✅ Loaded {count} STOCKS relationships\n")
        return count
    
    def load_disaster_impacts(self):
        """Load AFFECTS relationships from disasters to entities"""
        print("💥 Loading disaster AFFECTS relationships...")
        csv_file = self.data_dir / "disasters.csv"
        
        if not csv_file.exists():
            print(f"   ⚠️  File not found: {csv_file}")
            return 0
        
        df = pd.read_csv(csv_file)
        
        with self.driver.session() as session:
            count = 0
            for _, row in df.iterrows():
                # Check if affected_entities exists and is not NaN
                if pd.isna(row['affected_entities']) or not row['affected_entities']:
                    print(f"   ⚠️  No affected entities for disaster {row['id']}")
                    continue
                
                # Convert to string and parse affected entities
                affected = str(row['affected_entities']).split(',')
                
                for entity_id in affected:
                    entity_id = entity_id.strip()
                    if not entity_id:
                        continue
                    
                    # Determine entity type from ID prefix
                    if entity_id.startswith('FACTORY'):
                        label = 'Factory'
                    elif entity_id.startswith('PORT'):
                        label = 'Port'
                    elif entity_id.startswith('WAREHOUSE'):
                        label = 'Warehouse'
                    else:
                        continue
                    
                    query = f"""
                        MATCH (d:Disaster {{id: $disaster_id}})
                        MATCH (e:{label} {{id: $entity_id}})
                        CREATE (d)-[r:AFFECTS {{
                            severity: $severity,
                            impact_date: $start_date
                        }}]->(e)
                    """
                    
                    try:
                        session.run(query,
                            disaster_id=row['id'],
                            entity_id=entity_id,
                            severity=row['severity'],
                            start_date=row['start_date']
                        )
                        count += 1
                    except Exception as e:
                        # Entity might not exist, skip silently
                        pass
        
        print(f"   ✅ Loaded {count} AFFECTS relationships\n")
        return count

    
    def get_statistics(self):
        """Get database statistics"""
        with self.driver.session() as session:
            # Node counts
            node_counts = {}
            for label in ['Factory', 'Port', 'Warehouse', 'Product', 'Disaster']:
                result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                node_counts[label] = result.single()['count']
            
            # Relationship counts
            rel_counts = {}
            for rel_type in ['SUPPLIES_TO', 'STOCKS', 'AFFECTS']:
                result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count")
                rel_counts[rel_type] = result.single()['count']
            
            return node_counts, rel_counts

def main():
    """Main execution"""
    print("\n" + "="*70)
    print("🚀 LOADING DATA TO NEO4J")
    print("="*70 + "\n")
    
    loader = Neo4jLoader(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    try:
        # Connect
        print("✅ Connected to Neo4j\n")
        
        # Clear and setup
        loader.clear_database()
        loader.create_constraints()
        
        # Load nodes
        print("="*70)
        print("STEP 1: LOADING NODES")
        print("="*70 + "\n")
        
        factories = loader.load_factories()
        ports = loader.load_ports()
        warehouses = loader.load_warehouses()
        products = loader.load_products()
        disasters = loader.load_disasters()
        
        # Load relationships
        print("="*70)
        print("STEP 2: LOADING RELATIONSHIPS")
        print("="*70 + "\n")
        
        supplies = loader.load_supply_relationships()
        stocks = loader.load_stock_relationships()
        affects = loader.load_disaster_impacts()
        
        # Statistics
        print("="*70)
        print("✅ DATA LOADING COMPLETE!")
        print("="*70 + "\n")
        
        node_counts, rel_counts = loader.get_statistics()
        
        print("📊 Database Statistics:\n")
        print("   Node Counts:")
        for label, count in node_counts.items():
            print(f"      {label}: {count:,}")
        
        print("\n   Relationship Counts:")
        for rel_type, count in rel_counts.items():
            print(f"      {rel_type}: {count:,}")
        
        print("\n🌐 Access Neo4j Browser:")
        print(f"   URL: http://localhost:7474")
        print(f"   Username: {NEO4J_USER}")
        print(f"   Password: {NEO4J_PASSWORD}")
        
        print("\n🔍 Try these queries:")
        print("   1. View sample factories:")
        print("      MATCH (f:Factory) RETURN f LIMIT 25")
        print("\n   2. View supply chain path:")
        print("      MATCH path = (f:Factory)-[:SUPPLIES_TO*1..3]->(w:Warehouse)")
        print("      RETURN path LIMIT 5")
        print("\n   3. View disaster impacts:")
        print("      MATCH (d:Disaster)-[:AFFECTS]->(n)")
        print("      RETURN d.type, d.severity, count(n) as affected_facilities")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        loader.close()

if __name__ == "__main__":
    main()
