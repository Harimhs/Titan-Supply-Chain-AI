#!/usr/bin/env python3
"""
LLM Response Generator - UNLEASHED VERSION 🔓
No arbitrary limits. Full data transparency.
"""
import json

class ResponseGenerator:
    """Generate natural language responses from structured data"""
    
    def __init__(self):
        print("✅ Response Generator initialized (Unrestricted Mode)")
    
    def generate_response(self, query_results):
        intent = query_results.get("intent", "general")
        data = query_results.get("data", {})
        
        # Dispatcher
        if intent == "risk_assessment": return self._generate_risk_response(data)
        elif intent == "route_optimization": return self._generate_route_response(data)
        elif intent == "ml_prediction": return self._generate_prediction_response(data)
        elif intent == "disaster_analysis": return self._generate_disaster_response(data)
        elif intent == "facility_query": return self._generate_facility_response(data)
        elif intent == "product_query": return self._generate_product_response(data)
        elif intent == "country_analysis": return self._generate_country_response(data)
        else: return self._generate_general_response(data)
    
    def _generate_risk_response(self, data):
        response = "## 🎯 Risk Assessment\n\n"
        if "facility_risk" in data:
            r = data["facility_risk"]
            response += f"**Facility:** {r['name']} ({r['city']}, {r['country']})\n"
            response += f"**Overall Risk:** {r['risk_level']} ({r['overall_risk_score']:.2f})\n\n"
            response += "**Risk Breakdown:**\n"
            for k, v in r['risk_components'].items():
                response += f"- {k.replace('_',' ').title()}: {v:.2f}\n"
        elif "top_risks" in data:
            response += "**🚨 High Priority Risk Targets:**\n"
            # NO LIMITS - Show all returned risks
            for f in data["top_risks"]:
                response += f"- **{f['name']}**: {f['risk_level']} Risk (Score: {f['overall_risk_score']})\n"
        return response

    def _generate_route_response(self, data):
        response = "## 🛣️ Route Logistics\n\n"
        if "routes" in data:
            response += f"**Analysis of {len(data['routes'])} Viable Paths:**\n\n"
            for r in data['routes']:
                response += f"**Option {r['route_number']} ({r['route_type']}):**\n"
                response += f"- Distance: {r['total_distance_km']:,.0f} km\n"
                response += f"- Time: {r['estimated_time_days']:.1f} days\n"
                response += f"- Path: {' → '.join(r['node_names'])}\n\n"
        return response

    def _generate_prediction_response(self, data):
        response = "## 📊 Predictive Analytics\n\n"
        if "prediction" in data:
            p = data["prediction"]
            response += f"**Target:** {p['product_id']} in {p['country']}\n"
            response += f"**Forecast:** {p['predicted_demand']:,} units\n"
            response += f"**Confidence:** {p['confidence_level']} ({p['lower_bound']:,} - {p['upper_bound']:,})\n"
            if "disaster_impact" in p:
                di = p["disaster_impact"]
                response += f"\n📉 **Disaster Impact Detected:**\n"
                response += f"- Pre-Disaster Baseline: {di['original_demand']:,}\n"
                response += f"- Net Drop: {di['drop_pct']:.1f}% due to supply chain volatility.\n"
        return response

    def _generate_facility_response(self, data):
        response = "## 🏭 Facility Intelligence\n\n"
        # Combine all types
        all_facs = []
        if "factories" in data: all_facs.extend([(x['f'], 'Factory') for x in data['factories']])
        if "warehouses" in data: all_facs.extend([(x['w'], 'Warehouse') for x in data['warehouses']])
        if "ports" in data: all_facs.extend([(x['p'], 'Port') for x in data['ports']])
        
        response += f"**Identified {len(all_facs)} Assets:**\n"
        for f, ftype in all_facs:
            status = f.get('operational_status', 'Active')
            status_icon = "🔴" if status == 'Disrupted' else "🟢"
            response += f"- {status_icon} **{f['name']}** ({ftype}): {f.get('city')}, {f.get('country')}\n"
        return response

    def _generate_product_response(self, data):
        response = "## 📦 Product Ecosystem\n\n"
        if "product_info" in data:
            for p in data["product_info"]['results']:
                response += f"**{p['metadata']['name']} ({p['metadata']['category']})**\n"
        
        if "supply_network" in data:
            response += "\n**🔗 Full Supply Chain Trace:**\n"
            for link in data["supply_network"]: # NO LIMITS
                response += f"- {link['factory_name']} ➔ {link['dest_name']} ({link['distance']:.0f} km)\n"
        return response

    def _generate_disaster_response(self, data):
        response = "## 🌪️ Threat Monitoring\n\n"
        if "active_disasters" in data:
            response += f"**Current Active Threats ({len(data['active_disasters'])}):**\n"
            for d in data["active_disasters"]:
                dis = d['d']
                response += f"- **{dis['type']}** in {dis['country']} (Severity: {dis.get('severity', 'Unknown')})\n"
        return response

    def _generate_country_response(self, data):
        return self._generate_general_response(data)

    def _generate_general_response(self, data):
        return f"## 🔍 Data Overview\n\nRaw Data Retrieved: {len(str(data))} bytes. Please refine query for specific analysis."