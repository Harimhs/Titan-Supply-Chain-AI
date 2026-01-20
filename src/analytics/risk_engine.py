#!/usr/bin/env python3
"""
Supply Chain Risk Assessment Engine - FIXED VERSION
Dynamic risk calculation with real-world factors
"""
import sys
from pathlib import Path
import math
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.graph.neo4j_client import Neo4jClient

class RiskAssessmentEngine:
    """Calculate and analyze supply chain risks"""
    
    def __init__(self):
        """Initialize risk engine"""
        self.neo4j_client = Neo4jClient()
        
        # Base country stability (0-1, higher is more stable)
        # NOTE: In production, fetch from World Bank API or similar
        self._base_country_stability = {
            "China": 0.8, "India": 0.7, "Japan": 0.95, "South Korea": 0.9,
            "Singapore": 0.95, "USA": 0.9, "Canada": 0.95, "Brazil": 0.6,
            "Argentina": 0.5, "Germany": 0.95, "UK": 0.9, "France": 0.85,
            "Italy": 0.75, "Poland": 0.8, "Russia": 0.4, "South Africa": 0.5,
            "Egypt": 0.4, "Australia": 0.95
        }
        
        # Economic activity multipliers (affects stability)
        self._economic_strength = {
            "China": 1.2, "USA": 1.3, "Germany": 1.1, "Japan": 1.0,
            "India": 0.9, "Brazil": 0.7, "Russia": 0.6
        }
        
        print("✅ Risk Assessment Engine initialized")
    
    def calculate_disaster_risk(self, facility_id, radius_km=500):
        """
        Calculate disaster risk score based on proximity to disasters
        FIXED: More nuanced distance decay
        
        Returns: 0-1 score (0 = no risk, 1 = extreme risk)
        """
        disasters = self.neo4j_client.get_disasters_near_facility(facility_id, radius_km)
        
        if not disasters:
            return 0.0
        
        severity_weights = {
            "Low": 0.15, 
            "Medium": 0.45, 
            "High": 0.75, 
            "Critical": 1.0
        }
        
        risk_score = 0.0
        
        for disaster_record in disasters:
            disaster = disaster_record['d']
            distance = disaster_record['distance_km']
            severity = disaster.get('severity', 'Medium')
            status = disaster.get('status', 'Active')
            
            # Skip resolved disasters (lower weight)
            if status == 'Resolved':
                continue
            elif status == 'Ongoing':
                status_multiplier = 1.2  # Active threats are worse
            else:
                status_multiplier = 1.0
            
            # FIXED: Non-linear distance decay (exponential)
            # Risk drops rapidly beyond 100km, slowly after that
            if distance < 50:
                distance_factor = 1.0  # Direct impact zone
            elif distance < 100:
                distance_factor = math.exp(-(distance - 50) / 50)  # Sharp drop
            else:
                distance_factor = math.exp(-(distance - 100) / 200)  # Gradual decline
            
            severity_weight = severity_weights.get(severity, 0.5)
            disaster_risk = distance_factor * severity_weight * status_multiplier
            risk_score += disaster_risk
        
        # Cap at 1.0
        return min(1.0, risk_score)
    
    def calculate_route_redundancy_score(self, facility_id):
        """
        Calculate route redundancy score
        FIXED: More granular scoring
        """
        routes = self.neo4j_client.get_factory_supply_routes(facility_id)
        num_routes = len(routes)
        
        # Analyze route diversity (unique destinations)
        unique_destinations = set()
        unique_countries = set()
        
        for route in routes:
            dest = route['destination']
            unique_destinations.add(dest['id'])
            unique_countries.add(dest.get('country', ''))
        
        # Score components
        route_count_score = min(1.0, num_routes / 5)  # Ideal: 5+ routes
        destination_diversity = len(unique_destinations) / max(1, num_routes)
        country_diversity = min(1.0, len(unique_countries) / 3)  # Ideal: 3+ countries
        
        # Weighted redundancy score
        redundancy = (
            route_count_score * 0.5 +
            destination_diversity * 0.3 +
            country_diversity * 0.2
        )
        
        return redundancy
    
    def calculate_country_risk(self, country):
        """
        Get country stability risk score
        FIXED: Dynamic calculation based on multiple factors
        """
        base_stability = self._base_country_stability.get(country, 0.5)
        
        # Adjust for economic strength
        economic_factor = self._economic_strength.get(country, 0.8)
        
        # Check for active disasters in country
        query = """
        MATCH (d:Disaster {country: $country, status: 'Active'})
        RETURN count(d) as disaster_count
        """
        result = self.neo4j_client.run_query(query, {"country": country})
        disaster_count = result[0]['disaster_count'] if result else 0
        
        # Each disaster reduces stability by 5%
        disaster_penalty = min(0.3, disaster_count * 0.05)
        
        # Calculate adjusted stability
        adjusted_stability = base_stability * economic_factor - disaster_penalty
        adjusted_stability = max(0.1, min(1.0, adjusted_stability))
        
        # Return risk (inverse of stability)
        return 1.0 - adjusted_stability
    
    def calculate_operational_risk(self, facility):
        """
        Calculate operational risk based on facility status
        FIXED: Added capacity utilization factor
        """
        status = facility.get('operational_status', 'Operational')
        capacity = facility.get('capacity', 1000)
        
        status_risk = {
            "Operational": 0.05,
            "Maintenance": 0.35,
            "Disrupted": 0.75,
            "Closed": 1.0
        }
        
        base_risk = status_risk.get(status, 0.3)
        
        # FIXED: Add capacity factor (low capacity = higher risk)
        if capacity < 500:
            capacity_factor = 1.3  # Small facilities are more vulnerable
        elif capacity > 2000:
            capacity_factor = 0.8  # Large facilities have more resources
        else:
            capacity_factor = 1.0
        
        return min(1.0, base_risk * capacity_factor)
    
    def assess_facility_risk(self, facility_id):
        """
        Comprehensive risk assessment for a facility
        FIXED: Better weighting and explanations
        """
        facility_data = self.neo4j_client.run_query(
            "MATCH (f {id: $id}) RETURN f, labels(f) as type",
            {"id": facility_id}
        )
        
        if not facility_data:
            return {"error": "Facility not found"}
        
        facility = facility_data[0]['f']
        facility_type = facility_data[0]['type'][0]
        
        # Calculate risk components
        disaster_risk = self.calculate_disaster_risk(facility_id)
        
        if facility_type == "Factory":
            redundancy_score = self.calculate_route_redundancy_score(facility_id)
            route_risk = 1.0 - redundancy_score
        else:
            route_risk = 0.2  # Lower weight for non-factories
        
        country_risk = self.calculate_country_risk(facility.get('country', ''))
        operational_risk = self.calculate_operational_risk(facility)
        
        # FIXED: Better weighted overall risk
        overall_risk = (
            disaster_risk * 0.40 +      # 40% - Most immediate threat
            route_risk * 0.25 +         # 25% - Supply continuity
            country_risk * 0.20 +       # 20% - Systemic risk
            operational_risk * 0.15     # 15% - Internal factors
        )
        
        # Risk classification
        if overall_risk < 0.25:
            risk_level = "Low"
            color = "green"
        elif overall_risk < 0.50:
            risk_level = "Medium"
            color = "yellow"
        elif overall_risk < 0.75:
            risk_level = "High"
            color = "orange"
        else:
            risk_level = "Critical"
            color = "red"
        
        # FIXED: More specific recommendations
        recommendations = []
        
        if disaster_risk > 0.6:
            recommendations.append({
                "priority": "Critical",
                "category": "Disaster",
                "action": "Implement emergency evacuation and backup procedures",
                "reason": f"High disaster proximity risk ({disaster_risk:.2f})"
            })
        elif disaster_risk > 0.3:
            recommendations.append({
                "priority": "High",
                "category": "Disaster",
                "action": "Review disaster preparedness and insurance coverage",
                "reason": f"Moderate disaster risk ({disaster_risk:.2f})"
            })
        
        if route_risk > 0.7:
            recommendations.append({
                "priority": "High",
                "category": "Supply Chain",
                "action": "Establish at least 2 additional supply routes immediately",
                "reason": f"Critical route redundancy gap ({route_risk:.2f})"
            })
        elif route_risk > 0.5:
            recommendations.append({
                "priority": "Medium",
                "category": "Supply Chain",
                "action": "Diversify supply routes to different regions",
                "reason": f"Limited route redundancy ({route_risk:.2f})"
            })
        
        if country_risk > 0.6:
            recommendations.append({
                "priority": "High",
                "category": "Geopolitical",
                "action": "Monitor country situation daily; prepare contingency plans",
                "reason": f"High country instability ({country_risk:.2f})"
            })
        
        if operational_risk > 0.5:
            recommendations.append({
                "priority": "Medium",
                "category": "Operations",
                "action": "Inspect facility and resolve operational issues",
                "reason": f"Elevated operational risk ({operational_risk:.2f})"
            })
        
        if not recommendations:
            recommendations.append({
                "priority": "Low",
                "category": "Monitoring",
                "action": "Continue routine monitoring and quarterly reviews",
                "reason": "All risk factors within acceptable range"
            })
        
        return {
            "facility_id": facility_id,
            "facility_type": facility_type,
            "name": facility.get('name', 'Unknown'),
            "city": facility.get('city', ''),
            "country": facility.get('country', ''),
            "capacity": facility.get('capacity', 0),
            "risk_components": {
                "disaster_proximity": round(disaster_risk, 3),
                "route_redundancy": round(route_risk, 3),
                "country_stability": round(country_risk, 3),
                "operational_status": round(operational_risk, 3)
            },
            "overall_risk_score": round(overall_risk, 3),
            "risk_level": risk_level,
            "risk_color": color,
            "recommendations": recommendations
        }
    
    def assess_country_risk(self, country):
        """Assess overall supply chain risk for a country"""
        factories = self.neo4j_client.get_factories_by_country(country, limit=100)
        
        if not factories:
            return {"error": f"No facilities found in {country}"}
        
        risk_scores = []
        high_risk_facilities = []
        
        for factory_record in factories:
            factory = factory_record['f']
            risk = self.assess_facility_risk(factory['id'])
            risk_scores.append(risk['overall_risk_score'])
            
            if risk['risk_level'] in ['High', 'Critical']:
                high_risk_facilities.append({
                    "id": factory['id'],
                    "name": factory['name'],
                    "risk_level": risk['risk_level'],
                    "risk_score": risk['overall_risk_score']
                })
        
        avg_risk = sum(risk_scores) / len(risk_scores)
        max_risk = max(risk_scores)
        
        return {
            "country": country,
            "total_facilities": len(factories),
            "average_risk_score": round(avg_risk, 3),
            "max_risk_score": round(max_risk, 3),
            "high_risk_facilities": len(high_risk_facilities),
            "high_risk_list": high_risk_facilities[:5],
            "base_stability": self._base_country_stability.get(country, 0.5)
        }
    
    def get_highest_risk_facilities(self, limit=10):
        """Get facilities with highest risk scores"""
        query = """
        MATCH (f)
        WHERE f:Factory OR f:Warehouse OR f:Port
        RETURN f.id as id, labels(f) as type
        LIMIT 100
        """
        
        facilities = self.neo4j_client.run_query(query)
        risk_profiles = []
        
        for facility in facilities:
            risk = self.assess_facility_risk(facility['id'])
            if 'error' not in risk:
                risk_profiles.append(risk)
        
        risk_profiles.sort(key=lambda x: x['overall_risk_score'], reverse=True)
        return risk_profiles[:limit]
    
    def close(self):
        """Close connections"""
        self.neo4j_client.close()
