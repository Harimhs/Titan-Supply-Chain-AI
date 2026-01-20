#!/usr/bin/env python3
"""
TITAN Dashboard Server - FINAL INTEGRATION
"""
import sys
from pathlib import Path
from flask import Flask, jsonify, request, render_template, send_file
from flask_cors import CORS
import traceback
import random
import json
import logging
from src.reports.titan_reports import TitanReportGenerator

logging.getLogger("neo4j").setLevel(logging.ERROR)

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.titan_brain import TitanBrain

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

print("\n🚀 TITAN SYSTEM ONLINE")
try:
    brain = TitanBrain()
except Exception as e:
    print(f"❌ BRAIN FAILURE: {e}")
    pass

# Fallback Coords (Same as before)
CITY_MAP = {
    "Shanghai": (31.23, 121.47), "Beijing": (39.90, 116.40), "Shenzhen": (22.54, 114.05),
    "Guangzhou": (23.12, 113.26), "Mumbai": (19.07, 72.87), "Delhi": (28.61, 77.20),
    "Bangalore": (12.97, 77.59), "Chennai": (13.08, 80.27), "Tokyo": (35.67, 139.65),
    "Osaka": (34.69, 135.50), "Seoul": (37.56, 126.97), "Singapore": (1.35, 103.81),
    "New York": (40.71, -74.00), "Los Angeles": (34.05, -118.24), "London": (51.50, -0.12)
}

def resolve_coords(node):
    try:
        lat, lon = node.get('lat'), node.get('lon')
        if lat and lon and str(lat) != 'None': return float(lat), float(lon)
        city = node.get('city')
        if city in CITY_MAP:
            base = CITY_MAP[city]
            return (base[0] + random.uniform(-0.05, 0.05), base[1] + random.uniform(-0.05, 0.05))
    except: pass
    return (20.0 + random.uniform(-10, 10), 100.0 + random.uniform(-10, 10))

@app.route('/api/download-report')
def download_report():
    try:
        print("📄 Generating PDF Report...")
        generator = TitanReportGenerator()
        pdf_path = generator.generate_report()
        return send_file(pdf_path, as_attachment=True)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
# ---------------------------

@app.route('/')
def home():
    return render_template('dashboard.html')

@app.route('/api/globe-data')
def get_globe_data():
    region = request.args.get('region', 'All')
    product = request.args.get('product', 'All')
    
    try:
        nodes = []
        node_lookup = {}
        
        # 1. FETCH NODES
        if product != 'All':
            query = """
            MATCH (f:Factory {product_type: $product})
            OPTIONAL MATCH (f)-[r:SUPPLIES_TO]->(target)
            WITH f, collect(target) as targets
            UNWIND ([f] + targets) as n
            RETURN distinct n.id as id, n.name as name, labels(n)[0] as type,
                   n.city as city, n.country as country, n.lat as lat, n.lon as lon,
                   n.product_type as product, n.operational_status as status
            """
            params = {"product": product}
        else:
            query = "MATCH (n) WHERE n:Factory OR n:Warehouse OR n:Port RETURN n.id as id, n.name as name, labels(n)[0] as type, n.city as city, n.country as country, n.lat as lat, n.lon as lon, n.product_type as product, n.operational_status as status LIMIT 2000"
            params = {}

        raw_nodes = brain.neo4j.run_query(query, params)
        colors = {"P1": "#00ff88", "P2": "#00bbff", "P3": "#ffdd00", "P4": "#ff8800", "P5": "#bb00ff"}

        for n in raw_nodes:
            country = n.get('country', '')
            if region == 'Asia' and country not in ["China", "India", "Japan", "South Korea", "Singapore", "Thailand"]: continue
            if region == 'North America' and country not in ["USA", "Canada", "Mexico"]: continue
            
            lat, lon = resolve_coords(n)
            status = n.get('status', 'Operational')
            is_down = status == 'Disrupted'
            
            color = "#ff0000" if is_down else ("#00ff88" if n['type']=='Factory' else "#ffffff")
            if not is_down and n['type'] == 'Factory': color = colors.get(n.get('product'), "#00ff88")
            
            node_data = {
                "id": n['id'], "name": n['name'], "type": n['type'],
                "lat": lat, "lon": lon, "color": color,
                "city": n.get('city', ''), "country": country,
                "status": status
            }
            nodes.append(node_data)
            node_lookup[n['id']] = node_data

        # 2. ROUTES
        r_query = """
        MATCH (a)-[r:SUPPLIES_TO]->(b) 
        RETURN a.id as src, b.id as tgt, r.status as r_status
        """
        raw_routes = brain.neo4j.run_query(r_query)
        routes = []
        
        for r in raw_routes:
            if r['src'] in node_lookup and r['tgt'] in node_lookup:
                src = node_lookup[r['src']]
                tgt = node_lookup[r['tgt']]
                is_blocked = src['status'] == 'Disrupted' or tgt['status'] == 'Disrupted' or r.get('r_status') == 'Blocked'
                routes.append({
                    "startLat": src['lat'], "startLng": src['lon'],
                    "endLat": tgt['lat'], "endLng": tgt['lon'],
                    "color": "rgba(255, 0, 0, 0.4)" if is_blocked else "rgba(255, 255, 255, 0.15)"
                })

        # 3. DISASTERS
        d_query = "MATCH (d:Disaster {status: 'Active'}) RETURN d"
        raw_disasters = brain.neo4j.run_query(d_query)
        disasters = []
        for row in raw_disasters:
            d = row['d']
            dlat, dlon = float(d.get('lat', 0)), float(d.get('lon', 0))
            if dlat != 0:
                disasters.append({"lat": dlat, "lon": dlon, "color": "red", "maxR": 15, "propagationSpeed": 4})

        return jsonify({"nodes": nodes, "routes": routes, "disasters": disasters})

    except Exception as e:
        return jsonify({"nodes": [], "error": str(e)})

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        user_query = request.json.get('query')
        response = brain.process_query(user_query)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"response": f"❌ Error: {str(e)}"}), 500

@app.route('/api/god-mode', methods=['POST'])
def trigger_god_mode():
    try:
        data = request.json
        # Rich report from Brain
        report = brain.trigger_god_mode_event(
            data.get('type'), float(data.get('lat')), float(data.get('lon')), 500
        )
        
        ml = report['ml_forecast_adjustment']
        
        sitrep = f"""
🚨 **CRITICAL INCIDENT REPORT: {report['event'].upper()}**

**📍 Location:** {report['location']} (Radius: {report['impact_radius']})
**💥 Impact Analysis:** {report['critical_nodes_offline']} Critical Nodes Offline.
**🚧 Logistics:** {report['routes_compromised']} Supply Routes Blocked.

**🤖 AI AUTONOMOUS ACTIONS:**
1. **Risk Engine:** Impact Zone Calculated.
2. **Route Optimizer:** Rerouting algorithms deployed for blocked paths.
3. **ML Predictor:** Demand Forecast for **{ml.get('product', 'Unknown')}** adjusted.
   - Baseline: {ml.get('baseline_demand', 0):,} units
   - Adjusted: {ml.get('adjusted_demand', 0):,} units
   - **Impact:** <span style='color:red'>{ml.get('volatility_impact', '0%')}</span>

**System Status:** SELF-HEALING PROTOCOLS ENGAGED.
"""
        return jsonify({"status": "success", "impact": report, "sitrep": sitrep})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("✅ TITAN DASHBOARD READY")
    app.run(host='0.0.0.0', port=5000, debug=True)