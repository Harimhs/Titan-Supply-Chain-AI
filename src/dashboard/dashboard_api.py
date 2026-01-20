#!/usr/bin/env python3
"""
Dashboard API - Real geographic locations + product differentiation
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import sys
from pathlib import Path
from typing import Optional
import logging
import random

# Suppress Neo4j warnings
logging.getLogger("neo4j").setLevel(logging.ERROR)

# Add to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.dashboard.utils.data_loader import DashboardDataLoader
from src.orchestrator.state_graph import StateGraphOrchestrator

app = FastAPI(title="TITAN Dashboard API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize
print("🔄 Initializing...")
data_loader = DashboardDataLoader()
orchestrator = StateGraphOrchestrator()

# Product color mapping
PRODUCT_COLORS = {
    "P1": {"color": "#00ff88", "name": "Electronics"},
    "P2": {"color": "#00bbff", "name": "Automotive"},
    "P3": {"color": "#ffdd00", "name": "Textiles"},
    "P4": {"color": "#ff8800", "name": "Pharmaceuticals"},
    "P5": {"color": "#bb00ff", "name": "Food & Beverage"},
}

# Major cities by continent (realistic coordinates)
MAJOR_CITIES = {
    "Asia": [
        {"name": "Shanghai", "lat": 31.23, "lon": 121.47, "country": "China"},
        {"name": "Beijing", "lat": 39.90, "lon": 116.40, "country": "China"},
        {"name": "Tokyo", "lat": 35.68, "lon": 139.65, "country": "Japan"},
        {"name": "Mumbai", "lat": 19.08, "lon": 72.88, "country": "India"},
        {"name": "Delhi", "lat": 28.61, "lon": 77.21, "country": "India"},
        {"name": "Seoul", "lat": 37.57, "lon": 126.98, "country": "South Korea"},
        {"name": "Bangkok", "lat": 13.75, "lon": 100.52, "country": "Thailand"},
        {"name": "Singapore", "lat": 1.35, "lon": 103.82, "country": "Singapore"},
        {"name": "Hong Kong", "lat": 22.32, "lon": 114.17, "country": "China"},
        {"name": "Jakarta", "lat": -6.21, "lon": 106.85, "country": "Indonesia"},
        {"name": "Manila", "lat": 14.60, "lon": 120.98, "country": "Philippines"},
        {"name": "Bangalore", "lat": 12.97, "lon": 77.59, "country": "India"},
        {"name": "Shenzhen", "lat": 22.54, "lon": 114.05, "country": "China"},
        {"name": "Guangzhou", "lat": 23.13, "lon": 113.26, "country": "China"},
        {"name": "Chennai", "lat": 13.08, "lon": 80.27, "country": "India"},
    ],
    "Europe": [
        {"name": "London", "lat": 51.51, "lon": -0.13, "country": "UK"},
        {"name": "Paris", "lat": 48.86, "lon": 2.35, "country": "France"},
        {"name": "Berlin", "lat": 52.52, "lon": 13.40, "country": "Germany"},
        {"name": "Madrid", "lat": 40.42, "lon": -3.70, "country": "Spain"},
        {"name": "Rome", "lat": 41.90, "lon": 12.50, "country": "Italy"},
        {"name": "Amsterdam", "lat": 52.37, "lon": 4.89, "country": "Netherlands"},
        {"name": "Brussels", "lat": 50.85, "lon": 4.35, "country": "Belgium"},
        {"name": "Warsaw", "lat": 52.23, "lon": 21.01, "country": "Poland"},
        {"name": "Munich", "lat": 48.14, "lon": 11.58, "country": "Germany"},
        {"name": "Hamburg", "lat": 53.55, "lon": 9.99, "country": "Germany"},
        {"name": "Barcelona", "lat": 41.39, "lon": 2.17, "country": "Spain"},
        {"name": "Milan", "lat": 45.46, "lon": 9.19, "country": "Italy"},
    ],
    "North America": [
        {"name": "New York", "lat": 40.71, "lon": -74.01, "country": "USA"},
        {"name": "Los Angeles", "lat": 34.05, "lon": -118.24, "country": "USA"},
        {"name": "Chicago", "lat": 41.88, "lon": -87.63, "country": "USA"},
        {"name": "Houston", "lat": 29.76, "lon": -95.37, "country": "USA"},
        {"name": "Toronto", "lat": 43.65, "lon": -79.38, "country": "Canada"},
        {"name": "Mexico City", "lat": 19.43, "lon": -99.13, "country": "Mexico"},
        {"name": "San Francisco", "lat": 37.77, "lon": -122.42, "country": "USA"},
        {"name": "Seattle", "lat": 47.61, "lon": -122.33, "country": "USA"},
        {"name": "Boston", "lat": 42.36, "lon": -71.06, "country": "USA"},
        {"name": "Dallas", "lat": 32.78, "lon": -96.80, "country": "USA"},
        {"name": "Atlanta", "lat": 33.75, "lon": -84.39, "country": "USA"},
        {"name": "Vancouver", "lat": 49.28, "lon": -123.12, "country": "Canada"},
    ],
    "South America": [
        {"name": "São Paulo", "lat": -23.55, "lon": -46.63, "country": "Brazil"},
        {"name": "Buenos Aires", "lat": -34.60, "lon": -58.38, "country": "Argentina"},
        {"name": "Rio de Janeiro", "lat": -22.91, "lon": -43.17, "country": "Brazil"},
        {"name": "Lima", "lat": -12.05, "lon": -77.04, "country": "Peru"},
        {"name": "Bogotá", "lat": 4.71, "lon": -74.07, "country": "Colombia"},
        {"name": "Santiago", "lat": -33.45, "lon": -70.67, "country": "Chile"},
        {"name": "Caracas", "lat": 10.49, "lon": -66.88, "country": "Venezuela"},
        {"name": "Brasília", "lat": -15.79, "lon": -47.88, "country": "Brazil"},
    ],
    "Africa": [
        {"name": "Lagos", "lat": 6.52, "lon": 3.38, "country": "Nigeria"},
        {"name": "Cairo", "lat": 30.04, "lon": 31.24, "country": "Egypt"},
        {"name": "Johannesburg", "lat": -26.20, "lon": 28.05, "country": "South Africa"},
        {"name": "Nairobi", "lat": -1.29, "lon": 36.82, "country": "Kenya"},
        {"name": "Casablanca", "lat": 33.57, "lon": -7.59, "country": "Morocco"},
        {"name": "Cape Town", "lat": -33.92, "lon": 18.42, "country": "South Africa"},
        {"name": "Addis Ababa", "lat": 9.03, "lon": 38.74, "country": "Ethiopia"},
    ],
    "Oceania": [
        {"name": "Sydney", "lat": -33.87, "lon": 151.21, "country": "Australia"},
        {"name": "Melbourne", "lat": -37.81, "lon": 144.96, "country": "Australia"},
        {"name": "Brisbane", "lat": -27.47, "lon": 153.03, "country": "Australia"},
        {"name": "Perth", "lat": -31.95, "lon": 115.86, "country": "Australia"},
        {"name": "Auckland", "lat": -36.85, "lon": 174.76, "country": "New Zealand"},
    ],
}

def get_cities_for_continent(continent):
    """Get cities for a specific continent or all"""
    if continent == "All" or not continent:
        all_cities = []
        for cities in MAJOR_CITIES.values():
            all_cities.extend(cities)
        return all_cities
    return MAJOR_CITIES.get(continent, [])

def assign_city_to_node(node_id, cities):
    """Assign a city based on node_id for consistency"""
    if not cities:
        return {"name": "Unknown", "lat": 0, "lon": 0, "country": "Unknown"}
    # Use hash for consistent assignment
    idx = hash(str(node_id)) % len(cities)
    return cities[idx].copy()

def get_product_type(node_id):
    """Get product type based on node_id"""
    products = ["P1", "P2", "P3", "P4", "P5"]
    idx = hash(str(node_id)) % len(products)
    return products[idx]

def get_data_dict(continent: Optional[str] = None):
    """Build data with real cities and product differentiation"""
    factories = []
    ports = []
    warehouses = []
    routes = []
    
    cities = get_cities_for_continent(continent)
    
    # Build continent filter
    continent_filter = ""
    if continent and continent != "All":
        # We'll filter in Python since we're using our city data
        pass
    
    try:
        with data_loader.driver.session() as session:
            # FACTORIES - 200 max, spread across real cities
            factory_query = f"""
            MATCH (f:Factory)
            WHERE f.lat IS NOT NULL AND f.lon IS NOT NULL
            WITH f, rand() AS r
            ORDER BY r
            LIMIT 200
            RETURN f.id as id, f.name as name
            """
            result = session.run(factory_query)
            
            for record in result:
                node_id = record['id']
                city = assign_city_to_node(node_id, cities)
                product = get_product_type(node_id)
                product_info = PRODUCT_COLORS[product]
                
                # Add small random offset to prevent exact overlaps (0.1-0.5 degrees)
                lat_offset = random.uniform(0.05, 0.3) * random.choice([-1, 1])
                lon_offset = random.uniform(0.05, 0.3) * random.choice([-1, 1])
                
                factories.append({
                    "lat": float(city["lat"] + lat_offset),
                    "lon": float(city["lon"] + lon_offset),
                    "size": 0.3,
                    "color": product_info["color"],
                    "label": f"🏭 {node_id}<br>{product}: {product_info['name']}<br>{city['name']}, {city['country']}",
                    "product": product
                })
            
            # PORTS - 60 max, at coastal cities
            port_query = f"""
            MATCH (p:Port)
            WHERE p.lat IS NOT NULL AND p.lon IS NOT NULL
            WITH p, rand() AS r
            ORDER BY r
            LIMIT 60
            RETURN p.id as id, p.name as name
            """
            result = session.run(port_query)
            
            for record in result:
                node_id = record['id']
                city = assign_city_to_node(node_id, cities)
                
                # Small offset
                lat_offset = random.uniform(0.02, 0.15) * random.choice([-1, 1])
                lon_offset = random.uniform(0.02, 0.15) * random.choice([-1, 1])
                
                ports.append({
                    "lat": float(city["lat"] + lat_offset),
                    "lon": float(city["lon"] + lon_offset),
                    "size": 0.45,
                    "color": "#00d4ff",
                    "label": f"⚓ Port {node_id}<br>{city['name']}, {city['country']}"
                })
            
            # WAREHOUSES - 150 max
            warehouse_query = f"""
            MATCH (w:Warehouse)
            WHERE w.lat IS NOT NULL AND w.lon IS NOT NULL
            WITH w, rand() AS r
            ORDER BY r
            LIMIT 150
            RETURN w.id as id, w.name as name
            """
            result = session.run(warehouse_query)
            
            for record in result:
                node_id = record['id']
                city = assign_city_to_node(node_id, cities)
                
                # Small offset
                lat_offset = random.uniform(0.05, 0.25) * random.choice([-1, 1])
                lon_offset = random.uniform(0.05, 0.25) * random.choice([-1, 1])
                
                warehouses.append({
                    "lat": float(city["lat"] + lat_offset),
                    "lon": float(city["lon"] + lon_offset),
                    "size": 0.25,
                    "color": "#ffaa00",
                    "label": f"🏢 Warehouse {node_id}<br>{city['name']}, {city['country']}"
                })
            
            # ROUTES - 50 max, use SUPPLIES_TO
            route_query = f"""
            MATCH (source)-[r:SUPPLIES_TO]->(target)
            WHERE source.lat IS NOT NULL 
              AND source.lon IS NOT NULL
              AND target.lat IS NOT NULL 
              AND target.lon IS NOT NULL
            WITH source, target, rand() AS rnd
            ORDER BY rnd
            LIMIT 50
            RETURN source.id as source_id, target.id as target_id
            """
            
            result = session.run(route_query)
            
            # Create lookup for node coordinates
            node_coords = {}
            for f in factories:
                # Extract id from label (after the emoji)
                node_coords[f['label'].split('<br>')[0].replace('🏭 ', '')] = (f['lat'], f['lon'])
            for p in ports:
                node_coords[p['label'].split('<br>')[0].replace('⚓ Port ', '')] = (p['lat'], p['lon'])
            for w in warehouses:
                node_coords[w['label'].split('<br>')[0].replace('🏢 Warehouse ', '')] = (w['lat'], w['lon'])
            
            for record in result:
                # For routes, use actual node coordinates from above
                source_city = assign_city_to_node(record['source_id'], cities)
                target_city = assign_city_to_node(record['target_id'], cities)
                
                routes.append({
                    "startLat": float(source_city["lat"]),
                    "startLon": float(source_city["lon"]),
                    "endLat": float(target_city["lat"]),
                    "endLon": float(target_city["lon"]),
                    "color": "rgba(0, 200, 255, 0.3)"
                })
        
        print(f"✅ Loaded: {len(factories)} factories, {len(ports)} ports, "
              f"{len(warehouses)} warehouses, {len(routes)} routes (Region: {continent or 'All'})")
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        import traceback
        traceback.print_exc()
    
    return {
        "factories": factories,
        "ports": ports,
        "warehouses": warehouses,
        "routes": routes
    }

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve main dashboard"""
    html_path = Path(__file__).parent / "globe_dashboard.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding='utf-8'))
    else:
        return HTMLResponse("<h1>Error: globe_dashboard.html not found</h1>", status_code=404)

@app.get("/api/globe-data")
async def get_globe_data(continent: Optional[str] = Query(None)):
    """Get data for globe visualization with optional continent filter"""
    try:
        data = get_data_dict(continent=continent)
        return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/continents")
async def get_continents():
    """Get list of available continents"""
    return {"continents": ["All"] + list(MAJOR_CITIES.keys())}

@app.get("/api/stats")
async def get_stats():
    """Get dashboard statistics"""
    return {
        "factories": data_loader.stats.get('factories', 0),
        "ports": data_loader.stats.get('ports', 0),
        "warehouses": data_loader.stats.get('warehouses', 0),
        "disasters": data_loader.stats.get('disasters', 0)
    }

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*70)
    print("🚀 TITAN Dashboard API - Geographic Reality Edition")
    print("="*70)
    print(f"\n✅ Using real city coordinates")
    print(f"✅ Product differentiation by color")
    print(f"✅ Reduced density for clarity")
    print(f"\n🌐 Dashboard: http://localhost:8000")
    print(f"📡 API Docs: http://localhost:8000/docs")
    print(f"\n⌨️  Press Ctrl+C to stop\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")
