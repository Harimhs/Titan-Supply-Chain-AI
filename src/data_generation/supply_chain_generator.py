#!/usr/bin/env python3
"""
Supply Chain Data Generator
Generates products, inventory, routes, ships, and disruptions
"""

import pandas as pd
import numpy as np
from pathlib import Path
from geopy.distance import geodesic
from scipy.spatial import cKDTree

# Create data directories
DATA_DIR = Path(__file__).parent.parent.parent / 'data'
RAW_DIR = DATA_DIR / 'raw'
PROCESSED_DIR = DATA_DIR / 'processed'
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def generate_products(count=100000):  # Reduced from 500K for faster generation
    """
    Generate product catalog with SKUs
    """
    print(f"   Generating {count:,} products...")
    
    categories = {
        'Electronics': {
            'subcats': ['Smartphone', 'Laptop', 'Tablet', 'TV', 'Smartwatch', 'Headphones'],
            'weight_range': (0.1, 5.0),
            'value_range': (50, 2000)
        },
        'Automotive': {
            'subcats': ['Engine Parts', 'Transmission', 'Battery', 'Tires', 'Electronics'],
            'weight_range': (1.0, 50.0),
            'value_range': (100, 5000)
        },
        'Clothing': {
            'subcats': ['Shirt', 'Pants', 'Shoes', 'Jacket', 'Dress', 'Accessories'],
            'weight_range': (0.2, 2.0),
            'value_range': (10, 300)
        },
        'Food': {
            'subcats': ['Packaged', 'Fresh', 'Frozen', 'Beverages', 'Snacks'],
            'weight_range': (0.1, 10.0),
            'value_range': (5, 100)
        },
        'Furniture': {
            'subcats': ['Chair', 'Table', 'Bed', 'Sofa', 'Cabinet', 'Desk'],
            'weight_range': (5.0, 100.0),
            'value_range': (100, 2000)
        },
    }
    
    products = []
    sku_id = 1
    
    items_per_category = count // len(categories)
    
    for category, details in categories.items():
        subcats = details['subcats']
        items_per_subcat = items_per_category // len(subcats)
        
        for subcat in subcats:
            for i in range(items_per_subcat):
                weight_min, weight_max = details['weight_range']
                value_min, value_max = details['value_range']
                
                products.append({
                    'sku': f'SKU-{sku_id:09d}',
                    'category': category,
                    'subcategory': subcat,
                    'name': f'{subcat} Model {i+1}',
                    'weight_kg': round(np.random.uniform(weight_min, weight_max), 2),
                    'value_usd': round(np.random.uniform(value_min, value_max), 2),
                    'hs_code': f'{np.random.randint(1000, 9999)}',
                    'origin_country': np.random.choice([
                        'China', 'USA', 'Germany', 'Japan', 'India', 'Vietnam', 
                        'South Korea', 'Taiwan', 'Thailand', 'Mexico'
                    ], p=[0.35, 0.15, 0.10, 0.10, 0.08, 0.07, 0.05, 0.04, 0.03, 0.03])
                })
                sku_id += 1
    
    df = pd.DataFrame(products)
    
    # Save
    output_path = RAW_DIR / 'products.csv'
    df.to_csv(output_path, index=False)
    print(f"   ✅ Generated {len(df):,} products → {output_path}")
    
    return df


def generate_inventory(products_df, warehouses_df, sample_size=50000):
    """
    Generate inventory records (sampled for performance)
    """
    print(f"   Generating inventory for {sample_size:,} warehouse-product combinations...")
    
    # Sample warehouses and products for manageable size
    sampled_warehouses = warehouses_df.sample(min(5000, len(warehouses_df)))
    
    inventory = []
    
    for _, wh in sampled_warehouses.iterrows():
        # Each warehouse has 10-20 random SKUs
        n_skus = np.random.randint(10, 20)
        sampled_skus = products_df.sample(n_skus)
        
        for _, product in sampled_skus.iterrows():
            inventory.append({
                'warehouse_id': wh['warehouse_id'],
                'sku': product['sku'],
                'quantity': np.random.randint(0, 5000),
                'reorder_point': np.random.randint(50, 500),
                'last_updated': pd.Timestamp.now().isoformat()
            })
    
    df = pd.DataFrame(inventory)
    
    # Save as Parquet (compressed)
    output_path = PROCESSED_DIR / 'inventory_snapshot.parquet'
    df.to_parquet(output_path, compression='snappy')
    print(f"   ✅ Generated {len(df):,} inventory records → {output_path}")
    
    return df


def find_nearest_nodes(source_node, target_df, n=5, max_distance_km=2000):
    """
    Find n nearest nodes using KDTree
    """
    # Build KDTree for fast spatial queries
    coords = np.array(list(zip(target_df['lat'], target_df['lon'])))
    tree = cKDTree(coords)
    
    source_coords = (source_node['lat'], source_node['lon'])
    distances, indices = tree.query(source_coords, k=min(n+10, len(target_df)))
    
    # Filter by max distance
    valid_neighbors = []
    for dist_deg, idx in zip(distances[1:], indices[1:]):  # Skip self
        target = target_df.iloc[idx]
        actual_dist_km = geodesic(
            (source_node['lat'], source_node['lon']),
            (target['lat'], target['lon'])
        ).km
        
        if actual_dist_km <= max_distance_km:
            valid_neighbors.append((idx, actual_dist_km))
        
        if len(valid_neighbors) >= n:
            break
    
    return [target_df.iloc[idx] for idx, _ in valid_neighbors]


def generate_routes(factories_df, ports_df, warehouses_df, sample_size=50000):
    """
    Generate supply chain routes (sampled for performance)
    """
    print(f"   Generating {sample_size:,} routes...")
    
    routes = []
    route_id = 1
    
    # Sample for manageable size
    sampled_factories = factories_df.sample(min(5000, len(factories_df)))
    sampled_ports = ports_df.sample(min(500, len(ports_df)))
    sampled_warehouses = warehouses_df.sample(min(5000, len(warehouses_df)))
    
    # 1. Factory → Port (10K routes)
    print("      Creating Factory → Port routes...")
    for _, factory in sampled_factories.head(2000).iterrows():
        nearest_ports = find_nearest_nodes(factory, sampled_ports, n=3, max_distance_km=1500)
        
        for port in nearest_ports:
            distance_km = geodesic(
                (factory['lat'], factory['lon']),
                (port['lat'], port['lon'])
            ).km
            
            routes.append({
                'route_id': f'RT-{route_id:08d}',
                'from_id': factory['factory_id'],
                'to_id': port['port_id'],
                'from_type': 'Factory',
                'to_type': 'Port',
                'mode': 'Truck',
                'distance_km': round(distance_km, 2),
                'time_days': round(distance_km / 500, 1),  # 500 km/day avg
                'cost_per_container': round(distance_km * 1.5, 2)
            })
            route_id += 1
    
    # 2. Port → Port (5K routes)
    print("      Creating Port → Port routes...")
    major_ports = sampled_ports[sampled_ports['tier'] == 'Tier1']
    for _, port1 in major_ports.head(30).iterrows():
        for _, port2 in major_ports.head(30).iterrows():
            if port1['port_id'] != port2['port_id']:
                distance_km = geodesic(
                    (port1['lat'], port1['lon']),
                    (port2['lat'], port2['lon'])
                ).km
                
                if distance_km < 15000:  # Only reasonable shipping distances
                    routes.append({
                        'route_id': f'RT-{route_id:08d}',
                        'from_id': port1['port_id'],
                        'to_id': port2['port_id'],
                        'from_type': 'Port',
                        'to_type': 'Port',
                        'mode': 'Ship',
                        'distance_km': round(distance_km, 2),
                        'time_days': round(distance_km / 800, 1),  # 800 km/day ship
                        'cost_per_container': round(distance_km * 0.8, 2)
                    })
                    route_id += 1
    
    # 3. Port → Warehouse (35K routes)
    print("      Creating Port → Warehouse routes...")
    for _, port in sampled_ports.head(200).iterrows():
        nearby_warehouses = find_nearest_nodes(port, sampled_warehouses, n=25, max_distance_km=800)
        
        for wh in nearby_warehouses:
            distance_km = geodesic(
                (port['lat'], port['lon']),
                (wh['lat'], wh['lon'])
            ).km
            
            routes.append({
                'route_id': f'RT-{route_id:08d}',
                'from_id': port['port_id'],
                'to_id': wh['warehouse_id'],
                'from_type': 'Port',
                'to_type': 'Warehouse',
                'mode': 'Truck',
                'distance_km': round(distance_km, 2),
                'time_days': round(distance_km / 400, 1),  # 400 km/day local
                'cost_per_container': round(distance_km * 2.0, 2)
            })
            route_id += 1
    
    df = pd.DataFrame(routes)
    
    # Save
    output_path = PROCESSED_DIR / 'routes.csv'
    df.to_csv(output_path, index=False)
    print(f"   ✅ Generated {len(df):,} routes → {output_path}")
    
    return df


def generate_disasters():
    """
    Generate disaster scenarios
    """
    print("   Generating disaster scenarios...")
    
    disasters = [
        {
            'event_id': 'DIS-001',
            'type': 'Earthquake',
            'location': 'Taiwan',
            'lat': 24.0,
            'lon': 121.0,
            'severity': 7.2,
            'date': '2024-12-21',
            'affected_radius_km': 200,
            'recovery_days': 14
        },
        {
            'event_id': 'DIS-002',
            'type': 'Port Strike',
            'location': 'Rotterdam Port',
            'lat': 51.9,
            'lon': 4.5,
            'severity': 'High',
            'date': '2024-11-15',
            'affected_radius_km': 50,
            'recovery_days': 7
        },
        {
            'event_id': 'DIS-003',
            'type': 'Typhoon',
            'location': 'Shanghai',
            'lat': 31.2,
            'lon': 121.5,
            'severity': 'Category 4',
            'date': '2024-09-10',
            'affected_radius_km': 300,
            'recovery_days': 10
        },
        {
            'event_id': 'DIS-004',
            'type': 'Factory Fire',
            'location': 'Shenzhen',
            'lat': 22.5,
            'lon': 114.1,
            'severity': 'Critical',
            'date': '2024-10-05',
            'affected_radius_km': 10,
            'recovery_days': 21
        },
        {
            'event_id': 'DIS-005',
            'type': 'Flood',
            'location': 'Mumbai',
            'lat': 19.0,
            'lon': 72.8,
            'severity': 'Severe',
            'date': '2024-07-20',
            'affected_radius_km': 100,
            'recovery_days': 12
        },
    ]
    
    df = pd.DataFrame(disasters)
    output_path = RAW_DIR / 'disasters.json'
    df.to_json(output_path, orient='records', indent=2)
    print(f"   ✅ Generated {len(df)} disaster scenarios → {output_path}")
    
    return df


def generate_ship_positions(count=10000):  # Reduced from 100K for performance
    """
    Generate ship positions
    """
    print(f"   Generating {count:,} ship positions...")
    
    ships = []
    for i in range(count):
        ships.append({
            'ship_id': f'SHIP-{i:06d}',
            'mmsi': np.random.randint(100000000, 999999999),
            'name': f'Vessel {i}',
            'lat': round(np.random.uniform(-60, 70), 6),
            'lon': round(np.random.uniform(-180, 180), 6),
            'speed_knots': round(np.random.uniform(5, 20), 1),
            'heading': round(np.random.uniform(0, 360), 1),
            'cargo_type': np.random.choice(['Container', 'Bulk', 'Tanker', 'RORO']),
            'timestamp': pd.Timestamp.now().isoformat()
        })
    
    df = pd.DataFrame(ships)
    output_path = RAW_DIR / 'ships.json'
    df.to_json(output_path, orient='records')
    print(f"   ✅ Generated {len(df):,} ships → {output_path}")
    
    return df


if __name__ == '__main__':
    print("Testing supply_chain_generator...")
    products = generate_products(1000)
    print("✅ Test complete!")
