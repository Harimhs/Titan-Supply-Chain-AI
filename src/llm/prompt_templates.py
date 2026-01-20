"""
Prompt Templates for LLM generation
"""

def cascade_analysis_prompt(cascade_data):
    """Generate prompt for cascade analysis"""
    return f"""
You are a supply chain analyst. Analyze this cascade impact:

Source: {cascade_data['nodes'][0]['name']} ({cascade_data['nodes'][0]['city']}, {cascade_data['nodes'][0]['country']})
Target: {cascade_data['nodes'][-1]['name']} ({cascade_data['nodes'][-1]['city']}, {cascade_data['nodes'][-1]['country']})

Supply Chain Path ({cascade_data['hops']} hops):
{' → '.join([f"{n['name']} ({n['type']})" for n in cascade_data['nodes']])}

Total Distance: {cascade_data['total_distance_km']:.0f} km
Total Time: {cascade_data['total_time_days']:.1f} days

Provide:
1. Critical chokepoints in this path
2. Estimated financial impact if source fails
3. Recommended mitigation actions

Keep response under 200 words.
"""

def disaster_impact_prompt(disaster_data, affected_facilities):
    """Generate prompt for disaster impact"""
    return f"""
Analyze this supply chain disaster:

Disaster: {disaster_data['name']}
Type: {disaster_data['type']}
Location: {disaster_data['location']}
Affected Facilities: {len(affected_facilities)}

Top Affected:
{chr(10).join([f"- {f['name']} ({f['type']}) in {f['city']}, {f['country']}" for f in affected_facilities[:5]])}

Provide:
1. Immediate impact assessment
2. Downstream effects (which products/warehouses affected)
3. Recovery timeline estimate

Keep response under 200 words.
"""
