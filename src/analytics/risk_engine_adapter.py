#!/usr/bin/env python3

"""
Risk Engine Adapter - Fixes operational_status mismatch
Your data has "Active" but risk_engine expects "Operational"
Place this in: src/analytics/risk_engine_adapter.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.analytics.risk_engine import RiskAssessmentEngine as OriginalRiskEngine

class RiskEngineAdapter(OriginalRiskEngine):
    """Adapter that converts 'Active' to 'Operational' before processing"""

    def calculate_operational_risk(self, facility):
        """
        FIXED: Convert Active -> Operational before calculation
        """
        # Map existing data format to expected format
        status = facility.get('operational_status', 'Active')

        # Convert your data format to expected format
        status_mapping = {
            'Active': 'Operational',
            'Maintenance': 'Maintenance',
            'Disrupted': 'Disrupted',
            'Closed': 'Closed'
        }

        # Create adapted facility dict
        adapted_facility = facility.copy()
        adapted_facility['operational_status'] = status_mapping.get(status, 'Operational')

        # Call parent method with adapted data
        return super().calculate_operational_risk(adapted_facility)

    def assess_facility_risk(self, facility_id):
        """Override to adapt facility data before processing"""
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
            route_risk = 0.2

        country_risk = self.calculate_country_risk(facility.get('country', ''))

        # ADAPTED: Use our fixed method
        operational_risk = self.calculate_operational_risk(facility)

        # Weighted overall risk
        overall_risk = (
            disaster_risk * 0.40 +
            route_risk * 0.25 +
            country_risk * 0.20 +
            operational_risk * 0.15
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

        # Recommendations
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
