#!/usr/bin/env python3
"""
Dynamic Disaster Generator
AI-powered realistic disaster scenario creation
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum
import random
from datetime import datetime, timedelta

from src.graph.neo4j_client import Neo4jClient
from src.llm.groq_client import GroqLLM  # ✅ Fixed


class DisasterType(Enum):
    EARTHQUAKE = "earthquake"
    TYPHOON = "typhoon"
    FLOOD = "flood"
    PORT_STRIKE = "port_strike"
    FACTORY_FIRE = "factory_fire"
    CYBER_ATTACK = "cyber_attack"
    PANDEMIC = "pandemic"


@dataclass
class DisasterConstraints:
    """Physical constraints for realistic disasters"""
    max_radius_km: int = 500
    max_severity: float = 10.0
    max_recovery_days: int = 90
    min_economic_impact: float = 1_000_000  # $1M
    max_economic_impact: float = 100_000_000_000  # $100B


class DynamicDisasterGenerator:
    """
    Generate realistic disasters with AI
    """
    
    def __init__(self):
        self.neo4j = Neo4jClient()
        self.llm = GroqLLM()
        self.constraints = DisasterConstraints()
        
        # Realistic disaster parameters
        self.disaster_profiles = {
            DisasterType.EARTHQUAKE: {
                "severity_range": (4.0, 9.0),  # Richter scale
                "radius_range": (50, 500),
                "recovery_range": (7, 90),
                "likelihood_regions": ["Asia-Pacific", "Americas"]
            },
            DisasterType.TYPHOON: {
                "severity_range": (1, 5),  # Category
                "radius_range": (100, 800),
                "recovery_range": (5, 30),
                "likelihood_regions": ["Asia-Pacific"]
            },
            DisasterType.PORT_STRIKE: {
                "severity_range": (1, 10),  # Days
                "radius_range": (10, 100),
                "recovery_range": (3, 21),
                "likelihood_regions": ["All"]
            },
        }
    
    def generate_disaster(
        self,
        disaster_type: DisasterType,
        location: str,
        severity: float = None,
        radius_km: int = None
    ) -> Dict:
        """
        Generate a realistic disaster scenario
        """
        profile = self.disaster_profiles.get(disaster_type)
        
        if not profile:
            raise ValueError(f"Unknown disaster type: {disaster_type}")
        
        # Auto-generate parameters if not provided
        if severity is None:
            severity = random.uniform(*profile["severity_range"])
        
        if radius_km is None:
            radius_km = random.randint(*profile["radius_range"])
        
        # Clamp to constraints
        radius_km = min(radius_km, self.constraints.max_radius_km)
        severity = min(severity, profile["severity_range"][1])
        
        # Get location coordinates
        location_data = self._get_location_coords(location)
        
        if not location_data:
            raise ValueError(f"Location not found: {location}")
        
        # Calculate affected facilities
        affected = self._calculate_affected_facilities(
            location_data["lat"],
            location_data["lon"],
            radius_km
        )
        
        # Estimate recovery time
        recovery_days = self._estimate_recovery_time(disaster_type, severity, len(affected))
        
        # Estimate economic impact
        economic_impact = self._estimate_economic_impact(disaster_type, severity, affected)
        
        # Generate narrative with AI
        narrative = self._generate_narrative(disaster_type, location, severity, recovery_days)
        
        disaster_id = f"DIS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return {
            "disaster_id": disaster_id,
            "type": disaster_type.value,
            "location": location,
            "lat": location_data["lat"],
            "lon": location_data["lon"],
            "severity": severity,
            "radius_km": radius_km,
            "date": datetime.now().isoformat(),
            "recovery_days": recovery_days,
            "affected_facilities": affected,
            "economic_impact_usd": economic_impact,
            "narrative": narrative
        }
    
    def _get_location_coords(self, location: str) -> Dict:
        """Get coordinates for a location"""
        query = """
        MATCH (n)
        WHERE n.name =~ $location OR n.city =~ $location
        RETURN n.lat as lat, n.lon as lon, n.name as name
        LIMIT 1
        """
        result = self.neo4j.query(query, {"location": f"(?i).*{location}.*"})  # ✅ Fixed
        return result[0] if result else None

    
    def _calculate_affected_facilities(self, lat: float, lon: float, radius_km: int) -> List[Dict]:
        """Find facilities within disaster radius"""
        query = """
        MATCH (n)
        WHERE (n:Factory OR n:Port OR n:Warehouse)
        WITH n, point.distance(
            point({latitude: $lat, longitude: $lon}),
            point({latitude: n.lat, longitude: n.lon})
        ) / 1000 as distance_km
        WHERE distance_km <= $radius_km
        RETURN labels(n)[0] as type, 
            coalesce(n.name, n.factory_id, n.port_id, n.warehouse_id) as id,
            distance_km
        ORDER BY distance_km
        """
        return self.neo4j.query(query, {  # ✅ Fixed
            "lat": lat,
            "lon": lon,
            "radius_km": radius_km
        })

    
    def _estimate_recovery_time(self, disaster_type: DisasterType, severity: float, affected_count: int) -> int:
        """Estimate recovery time based on severity"""
        profile = self.disaster_profiles[disaster_type]
        base_recovery = sum(profile["recovery_range"]) / 2
        
        # Adjust for severity
        severity_factor = severity / profile["severity_range"][1]
        
        # Adjust for scale
        scale_factor = min(affected_count / 100, 2.0)
        
        recovery_days = int(base_recovery * severity_factor * scale_factor)
        
        return min(recovery_days, self.constraints.max_recovery_days)
    
    def _estimate_economic_impact(self, disaster_type: DisasterType, severity: float, affected: List) -> float:
        """Estimate economic impact"""
        # Base impact per facility type
        impact_per_facility = {
            "Factory": 5_000_000,
            "Port": 50_000_000,
            "Warehouse": 2_000_000
        }
        
        total_impact = 0
        for facility in affected:
            base = impact_per_facility.get(facility["type"], 1_000_000)
            total_impact += base * (severity / 5.0)  # Scale by severity
        
        return min(total_impact, self.constraints.max_economic_impact)
    
    def _generate_narrative(self, disaster_type: DisasterType, location: str, severity: float, recovery_days: int) -> str:
        """Generate disaster narrative with AI"""
        prompt = f"""
Generate a realistic news headline and brief description for this disaster:

Type: {disaster_type.value}
Location: {location}
Severity: {severity:.1f}
Est. Recovery: {recovery_days} days

Format:
Headline: ...
Description: 2-3 sentences about impact on supply chain.

Be realistic and professional.
"""
        return self.llm.generate(prompt, temperature=0.7)
    
    def insert_into_neo4j(self, disaster: Dict):
        """Insert generated disaster into Neo4j"""
        query = """
        CREATE (d:Disaster {
            disaster_id: $disaster_id,
            event_id: $disaster_id,
            type: $type,
            location_name: $location,
            lat: $lat,
            lon: $lon,
            severity: $severity,
            radius_km: $radius_km,
            date: $date,
            recovery_days: $recovery_days,
            economic_impact_usd: $economic_impact_usd,
            narrative: $narrative
        })
        RETURN d
        """
        # Pass the disaster dict directly - Neo4j will match keys
        self.neo4j.query(query, {
            "disaster_id": disaster["disaster_id"],
            "type": disaster["type"],
            "location": disaster["location"],
            "lat": disaster["lat"],
            "lon": disaster["lon"],
            "severity": disaster["severity"],
            "radius_km": disaster["radius_km"],
            "date": disaster["date"],
            "recovery_days": disaster["recovery_days"],
            "economic_impact_usd": disaster["economic_impact_usd"],  # ✅ Fixed key name
            "narrative": disaster["narrative"]
        })
        
        # Link to affected facilities
        self._link_affected_facilities(disaster)


    
    def _link_affected_facilities(self, disaster: Dict):
        """Create AFFECTS relationships"""
        query = """
        MATCH (d:Disaster {disaster_id: $disaster_id})
        MATCH (n)
        WHERE (n:Factory OR n:Port OR n:Warehouse)
        WITH d, n, point.distance(
            point({latitude: d.lat, longitude: d.lon}),
            point({latitude: n.lat, longitude: n.lon})
        ) / 1000 as distance_km
        WHERE distance_km <= d.radius_km
        CREATE (d)-[:AFFECTS {distance_km: distance_km}]->(n)
        """
        self.neo4j.query(query, {"disaster_id": disaster["disaster_id"]})  # ✅ Fixed



# ============================================================================
# USAGE EXAMPLE
# ============================================================================

def test_disaster_generator():
    """Test dynamic disaster generation"""
    generator = DynamicDisasterGenerator()
    
    # User-defined disaster
    print("\n🌪️  Generating Typhoon in Singapore...")
    disaster = generator.generate_disaster(
        disaster_type=DisasterType.TYPHOON,
        location="Singapore",
        severity=4.0,  # Category 4
        radius_km=200
    )
    
    print(f"\n✅ Generated Disaster:")
    print(f"   ID: {disaster['disaster_id']}")
    print(f"   Type: {disaster['type']}")
    print(f"   Severity: {disaster['severity']}")
    print(f"   Radius: {disaster['radius_km']} km")
    print(f"   Recovery: {disaster['recovery_days']} days")
    print(f"   Affected: {len(disaster['affected_facilities'])} facilities")
    print(f"   Economic Impact: ${disaster['economic_impact_usd']:,.0f}")
    print(f"\n   Narrative:\n{disaster['narrative']}")
    
    # Insert into Neo4j
    generator.insert_into_neo4j(disaster)
    print(f"\n✅ Inserted into Neo4j")


if __name__ == "__main__":
    test_disaster_generator()
