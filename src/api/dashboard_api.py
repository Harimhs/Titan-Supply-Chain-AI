#!/usr/bin/env python3
"""
Dashboard API Endpoints
Serves data for Globe.gl visualization
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import sys
from pathlib import Path
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.dashboard.utils.data_loader import DashboardDataLoader

app = FastAPI(title="TITAN Dashboard API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize data loader globally
print("🔄 Initializing data loader...")
data_loader = DashboardDataLoader()
print(f"✅ Data loaded: {len(data_loader.factories)} factories, {len(data_loader.ports)} ports")


@app.get("/")
async def root():
    """Serve main dashboard"""
    html_path = Path(__file__).parent.parent / "dashboard" / "globe_dashboard.html"
    return HTMLResponse(content=html_path.read_text(encoding='utf-8'))

@app.get("/api/dashboard/data")
async def get_dashboard_data():
    """Get all dashboard data"""
    print("🔍 API endpoint called")
    
    try:
        # Sample working routes (hardcoded for demo reliability)
        sample_routes = [
            # Major supply routes
            {"startLat": 31.2, "startLon": 121.5, "endLat": 19.0, "endLon": 72.8, "color": "rgba(0,255,242,0.4)"},  # Shanghai to Mumbai
            {"startLat": 22.3, "startLon": 114.2, "endLat": 1.3, "endLon": 103.8, "color": "rgba(0,255,242,0.4)"},   # Hong Kong to Singapore
            {"startLat": 35.7, "startLon": 139.7, "endLat": 34.0, "endLon": -118.2, "color": "rgba(0,255,242,0.4)"}, # Tokyo to LA
            {"startLat": 51.5, "startLon": -0.1, "endLat": 40.7, "endLon": -74.0, "color": "rgba(0,255,242,0.4)"},   # London to NYC
            {"startLat": 28.6, "startLon": 77.2, "endLat": 19.0, "endLon": 72.8, "color": "rgba(0,255,242,0.4)"},    # Delhi to Mumbai
        ]
        
        data = {
            "factories": [
                {
                    "lat": float(row['lat']),
                    "lon": float(row['lon']),
                    "size": 1.5,
                    "color": "#00ff88",
                    "label": f"🏭 {row['id']}<br>{row.get('region', 'Unknown')}"
                }
                for _, row in data_loader.factories.iterrows()
            ],
            "ports": [
                {
                    "lat": float(row['lat']),
                    "lon": float(row['lon']),
                    "size": 3.0,
                    "color": "#00bbff",
                    "label": f"⚓ {row.get('name', row['id'])}<br>{row.get('city', 'Unknown')}"
                }
                for _, row in data_loader.ports.iterrows()
            ],
            "warehouses": [
                {
                    "lat": float(row['lat']),
                    "lon": float(row['lon']),
                    "size": 1.0,
                    "color": "#ffaa00",
                    "label": f"🏢 {row['id']}<br>{row.get('city', 'Unknown')}"
                }
                for _, row in data_loader.warehouses.iterrows()
            ],
            "disasters": [
                {
                    "lat": float(row['lat']),
                    "lon": float(row['lon']),
                    "size": 5.0,
                    "color": "#ff3333",
                    "label": f"🔥 {row.get('location', 'Unknown')}<br>{row.get('type', 'Unknown')}"
                }
                for _, row in data_loader.disasters.iterrows()
            ],
            "routes": sample_routes  # Use reliable sample routes
        }
        
        print(f"✅ Returning: {len(data['factories'])} factories, {len(data['routes'])} routes")
        return JSONResponse(content=data)
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_stats():
    """Get supply chain statistics"""
    return JSONResponse(content=data_loader.stats)


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting TITAN Dashboard API...")
    print("📡 Dashboard: http://localhost:8000")
    print("📊 API Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
