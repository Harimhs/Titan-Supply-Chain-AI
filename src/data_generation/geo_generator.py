#!/usr/bin/env python3
"""
Geography Data Generator
Generates factories, ports, and warehouses
"""

import pandas as pd
import numpy as np
from pathlib import Path
from shapely.geometry import Point
import geopandas as gpd

# Create data directories
DATA_DIR = Path(__file__).parent.parent.parent / 'data'
RAW_DIR = DATA_DIR / 'raw'
RAW_DIR.mkdir(parents=True, exist_ok=True)


def generate_factories(count=50000):
    """
    Generate 50,000 factories worldwide based on real industrial regions
    """
    print(f"   Generating {count:,} factories...")
    
    # Manufacturing hotspots (lat, lon, factory_count)
    regions = {
        'China_East': (31.2, 121.5, 12000),       # Shanghai
        'China_South': (23.1, 113.3, 8000),       # Guangzhou
        'China_North': (39.9, 116.4, 5000),       # Beijing
        'India_South': (13.0, 80.2, 3500),        # Chennai/Coimbatore
        'India_West': (19.0, 72.8, 2500),         # Mumbai
        'India_North': (28.6, 77.2, 2000),        # Delhi
        'EU_Germany': (51.2, 10.4, 4000),         # Germany
        'EU_Italy': (45.5, 9.2, 2000),            # Milan
        'USA_East': (40.7, -74.0, 3000),          # New York
        'USA_West': (34.0, -118.2, 2500),         # LA
        'USA_Midwest': (41.9, -87.6, 2000),       # Chicago
        'Vietnam': (21.0, 105.8, 3500),           # Hanoi
        'Thailand': (13.7, 100.5, 2000),          # Bangkok
        'Mexico': (19.4, -99.1, 2000),            # Mexico City
        'Brazil': (-23.5, -46.6, 1500),           # Sao Paulo
        'Japan': (35.7, 139.7, 1500),             # Tokyo
        'South_Korea': (37.6, 127.0, 1000),       # Seoul
    }
    
    factories = []
    factory_id = 1
    
    for region_name, (base_lat, base_lon, region_count) in regions.items():
        for _ in range(region_count):
            # Gaussian distribution around hotspot (±150km radius)
            lat = np.random.normal(base_lat, 1.5)
            lon = np.random.normal(base_lon, 1.5)
            
            factories.append({
                'factory_id': f'FAC-{factory_id:06d}',
                'name': f'Factory {factory_id}',
                'region': region_name,
                'lat': round(lat, 6),
                'lon': round(lon, 6),
                'tier': np.random.choice([1, 2, 3, 4], p=[0.1, 0.2, 0.3, 0.4]),
                'capacity_units_per_day': np.random.randint(1000, 50000),
                'specialization': np.random.choice([
                    'Electronics', 'Automotive', 'Textiles', 'Pharmaceuticals',
                    'Food', 'Machinery', 'Chemicals', 'Furniture', 'Plastics'
                ], p=[0.25, 0.20, 0.15, 0.10, 0.10, 0.08, 0.07, 0.03, 0.02]),
                'operational_status': np.random.choice(['Active', 'Limited', 'Maintenance'], p=[0.90, 0.08, 0.02])
            })
            factory_id += 1
    
    df = pd.DataFrame(factories)
    
    # Convert to GeoDataFrame
    geometry = [Point(xy) for xy in zip(df.lon, df.lat)]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:4326')
    
    # Save
    output_path = RAW_DIR / 'factories.geojson'
    gdf.to_file(output_path, driver='GeoJSON')
    print(f"   ✅ Generated {len(df):,} factories → {output_path}")
    
    return df


def generate_ports(count=2000):
    """
    Generate 2,000 ports worldwide
    """
    print(f"   Generating {count:,} ports...")
    
    # Major global ports (name, lat, lon, tier, annual_TEU)
    major_ports = [
        ('Shanghai', 31.2304, 121.4737, 'Tier1', 47030000),
        ('Singapore', 1.2897, 103.8501, 'Tier1', 37200000),
        ('Ningbo-Zhoushan', 29.8683, 121.5440, 'Tier1', 33350000),
        ('Shenzhen', 22.5431, 114.0579, 'Tier1', 30000000),
        ('Guangzhou', 23.1291, 113.2644, 'Tier1', 24200000),
        ('Busan', 35.1796, 129.0756, 'Tier1', 22000000),
        ('Hong Kong', 22.3193, 114.1694, 'Tier1', 17800000),
        ('Qingdao', 36.0986, 120.3719, 'Tier1', 21000000),
        ('Dubai', 25.2769, 55.2963, 'Tier1', 14100000),
        ('Tianjin', 39.0851, 117.1993, 'Tier1', 18350000),
        ('Rotterdam', 51.9244, 4.4777, 'Tier1', 14500000),
        ('Port Klang', 2.9983, 101.3894, 'Tier1', 13600000),
        ('Antwerp', 51.2194, 4.4025, 'Tier1', 12000000),
        ('Xiamen', 24.4798, 118.0894, 'Tier1', 11300000),
        ('Kaohsiung', 22.6273, 120.3014, 'Tier1', 10260000),
        ('Los Angeles', 33.7405, -118.2703, 'Tier1', 9700000),
        ('Tanjung Pelepas', 1.3644, 103.5483, 'Tier1', 10500000),
        ('Hamburg', 53.5511, 9.9937, 'Tier2', 8700000),
        ('Long Beach', 33.7701, -118.1937, 'Tier2', 8100000),
        ('Laem Chabang', 13.0827, 100.8831, 'Tier2', 7700000),
        ('New York/New Jersey', 40.6895, -74.0446, 'Tier2', 7500000),
        ('Mumbai', 18.9480, 72.8267, 'Tier2', 5000000),
        ('Chennai', 13.0827, 80.2707, 'Tier2', 1900000),
        ('Jawaharlal Nehru (Mumbai)', 18.9671, 72.9512, 'Tier2', 5400000),
        ('Colombo', 6.9271, 79.8612, 'Tier2', 7200000),
        ('Ho Chi Minh City', 10.7769, 106.7009, 'Tier2', 7500000),
        ('Manila', 14.5995, 120.9842, 'Tier2', 4600000),
        ('Jakarta', -6.1045, 106.8779, 'Tier2', 6000000),
        ('Sydney', -33.8688, 151.2093, 'Tier2', 2600000),
        ('Melbourne', -37.8136, 144.9631, 'Tier2', 2900000),
    ]
    
    ports = []
    port_id = 1
    
    # Add major ports
    for name, lat, lon, tier, teu in major_ports:
        ports.append({
            'port_id': f'PRT-{port_id:04d}',
            'name': name,
            'lat': round(lat, 6),
            'lon': round(lon, 6),
            'tier': tier,
            'annual_TEU': teu,
            'congestion_index': round(np.random.uniform(0.3, 0.9), 2),
            'berth_count': np.random.randint(10, 50),
            'max_vessel_size': 'Ultra Large'
        })
        port_id += 1
    
    # Generate additional regional/smaller ports
    remaining = count - len(major_ports)
    
    # Coastal regions for port generation
    coastal_regions = [
        ('East Asia', 20, 120, remaining // 4),
        ('Southeast Asia', 5, 105, remaining // 6),
        ('Europe', 50, 10, remaining // 6),
        ('North America', 35, -75, remaining // 6),
        ('South America', -20, -50, remaining // 8),
        ('Africa', 0, 30, remaining // 8),
        ('Oceania', -25, 145, remaining // 10),
    ]
    
    for region, base_lat, base_lon, region_count in coastal_regions:
        for _ in range(region_count):
            ports.append({
                'port_id': f'PRT-{port_id:04d}',
                'name': f'{region} Port {port_id}',
                'lat': round(np.random.normal(base_lat, 10), 6),
                'lon': round(np.random.normal(base_lon, 15), 6),
                'tier': np.random.choice(['Tier2', 'Tier3'], p=[0.3, 0.7]),
                'annual_TEU': np.random.randint(50000, 2000000),
                'congestion_index': round(np.random.uniform(0.1, 0.7), 2),
                'berth_count': np.random.randint(3, 15),
                'max_vessel_size': np.random.choice(['Large', 'Medium', 'Small'], p=[0.3, 0.5, 0.2])
            })
            port_id += 1
    
    df = pd.DataFrame(ports)
    
    # Convert to GeoDataFrame
    geometry = [Point(xy) for xy in zip(df.lon, df.lat)]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:4326')
    
    # Save
    output_path = RAW_DIR / 'ports.geojson'
    gdf.to_file(output_path, driver='GeoJSON')
    print(f"   ✅ Generated {len(df):,} ports → {output_path}")
    
    return df


def generate_warehouses(count=100000):  # Reduced from 500K for faster generation
    """
    Generate warehouses near major cities
    """
    print(f"   Generating {count:,} warehouses...")
    
    # Major cities with warehouse clusters (city, lat, lon, warehouse_count)
    cities = {
        'Mumbai': (19.0760, 72.8777, 8000),
        'Delhi': (28.7041, 77.1025, 7000),
        'Bangalore': (12.9716, 77.5946, 5000),
        'Chennai': (13.0827, 80.2707, 4500),
        'Coimbatore': (11.0168, 76.9558, 3000),
        'Shanghai': (31.2304, 121.4737, 9000),
        'Beijing': (39.9042, 116.4074, 7000),
        'Shenzhen': (22.5431, 114.0579, 6000),
        'New York': (40.7128, -74.0060, 8000),
        'Los Angeles': (34.0522, -118.2437, 7500),
        'Chicago': (41.8781, -87.6298, 5000),
        'London': (51.5074, -0.1278, 6000),
        'Paris': (48.8566, 2.3522, 4000),
        'Berlin': (52.5200, 13.4050, 3500),
        'Tokyo': (35.6762, 139.6503, 6500),
        'Singapore': (1.3521, 103.8198, 4500),
        'Dubai': (25.2048, 55.2708, 4000),
        'Sydney': (-33.8688, 151.2093, 3000),
        'Toronto': (43.6532, -79.3832, 3500),
        'Mexico City': (19.4326, -99.1332, 3000),
    }
    
    warehouses = []
    wh_id = 1
    
    for city, (base_lat, base_lon, city_count) in cities.items():
        for _ in range(city_count):
            # Distribute around city (±50km)
            lat = np.random.normal(base_lat, 0.5)
            lon = np.random.normal(base_lon, 0.5)
            
            warehouses.append({
                'warehouse_id': f'WH-{wh_id:06d}',
                'name': f'{city} Warehouse {wh_id}',
                'city': city,
                'lat': round(lat, 6),
                'lon': round(lon, 6),
                'type': np.random.choice([
                    'Fulfillment', 'Distribution', 'Dark Store', 'Cross-Dock', 'Cold Storage'
                ], p=[0.35, 0.30, 0.15, 0.12, 0.08]),
                'capacity_sqft': np.random.randint(10000, 500000),
                'owner': np.random.choice([
                    'Amazon', 'Flipkart', 'Walmart', 'DHL', 'FedEx', 'Blue Dart', 'Private'
                ], p=[0.18, 0.12, 0.15, 0.10, 0.08, 0.07, 0.30]),
                'automation_level': np.random.choice(['High', 'Medium', 'Low'], p=[0.2, 0.5, 0.3])
            })
            wh_id += 1
    
    df = pd.DataFrame(warehouses)
    
    # Convert to GeoDataFrame
    geometry = [Point(xy) for xy in zip(df.lon, df.lat)]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:4326')
    
    # Save
    output_path = RAW_DIR / 'warehouses.geojson'
    gdf.to_file(output_path, driver='GeoJSON')
    print(f"   ✅ Generated {len(df):,} warehouses → {output_path}")
    
    return df


if __name__ == '__main__':
    print("Testing geo_generator...")
    factories = generate_factories(1000)
    ports = generate_ports(50)
    warehouses = generate_warehouses(500)
    print("✅ Test complete!")
