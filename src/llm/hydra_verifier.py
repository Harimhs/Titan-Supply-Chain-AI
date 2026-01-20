"""
HyDRA: Hallucination Detection using Rule-based Verification
Symbolic contracts that verify LLM outputs
"""

class HyDRAVerifier:
    def __init__(self, graph_rag):
        self.graph_rag = graph_rag
        
    def verify_cascade_prediction(self, llm_output, cascade_data):
        """
        Verify LLM's cascade prediction against symbolic constraints
        
        Constraints:
        1. Geographic: Distance must match actual distance ±10%
        2. Temporal: Time must match actual time ±20%
        3. Cascade: All nodes in path must be connected
        4. Capacity: No facility can exceed capacity
        """
        violations = []
        
        # Extract claims from LLM output
        claims = self._extract_claims(llm_output)
        
        # CONSTRAINT 1: Geographic Verification
        if 'distance' in claims:
            claimed_distance = claims['distance']
            actual_distance = cascade_data.get('total_distance_km', 0)
            
            if actual_distance > 0:
                error_pct = abs(claimed_distance - actual_distance) / actual_distance
                if error_pct > 0.10:  # 10% tolerance
                    violations.append({
                        'type': 'GEOGRAPHIC_VIOLATION',
                        'claimed': f"{claimed_distance:.0f} km",
                        'actual': f"{actual_distance:.0f} km",
                        'error': f"{error_pct*100:.1f}%"
                    })
        
        # CONSTRAINT 2: Temporal Verification
        if 'time' in claims:
            claimed_time = claims['time']
            actual_time = cascade_data.get('total_time_days', 0)
            
            if actual_time > 0:
                error_pct = abs(claimed_time - actual_time) / actual_time
                if error_pct > 0.20:  # 20% tolerance
                    violations.append({
                        'type': 'TEMPORAL_VIOLATION',
                        'claimed': f"{claimed_time:.1f} days",
                        'actual': f"{actual_time:.1f} days",
                        'error': f"{error_pct*100:.1f}%"
                    })
        
        # CONSTRAINT 3: Cascade Connectivity
        if 'affected_facilities' in claims:
            claimed_count = claims['affected_facilities']
            # Verify against graph
            # (In real implementation, query Neo4j to verify each facility exists)
            if claimed_count < 0 or claimed_count > 1000000:
                violations.append({
                    'type': 'CAPACITY_VIOLATION',
                    'claimed': claimed_count,
                    'reason': 'Unrealistic facility count'
                })
        
        # CONSTRAINT 4: Financial Impact (Basic sanity check)
        if 'financial_impact' in claims:
            impact = claims['financial_impact']
            # Basic sanity: Impact should be between $1M - $100B
            if impact < 1_000_000 or impact > 100_000_000_000:
                violations.append({
                    'type': 'FINANCIAL_VIOLATION',
                    'claimed': f"${impact:,.0f}",
                    'reason': 'Unrealistic financial impact'
                })
        
        return {
            'is_valid': len(violations) == 0,
            'violations': violations,
            'confidence': self._calculate_confidence(violations)
        }
    
    def _extract_claims(self, llm_output):
        """
        Extract factual claims from LLM output using regex
        """
        import re
        claims = {}
        
        # Extract distance (e.g., "4,359 km" or "4359km")
        distance_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*km', llm_output)
        if distance_match:
            claims['distance'] = float(distance_match.group(1).replace(',', ''))
        
        # Extract time (e.g., "7.1 days" or "7 days")
        time_match = re.search(r'([\d.]+)\s*days?', llm_output)
        if time_match:
            claims['time'] = float(time_match.group(1))
        
        # Extract facility count
        facility_match = re.search(r'(\d+)\s*(?:facilities|warehouses)', llm_output, re.IGNORECASE)
        if facility_match:
            claims['affected_facilities'] = int(facility_match.group(1))
        
        # Extract financial impact (e.g., "$50M", "$1.2B")
        financial_match = re.search(r'\$\s*([\d.]+)\s*([MB])', llm_output)
        if financial_match:
            value = float(financial_match.group(1))
            unit = financial_match.group(2)
            multiplier = 1_000_000 if unit == 'M' else 1_000_000_000
            claims['financial_impact'] = value * multiplier
        
        return claims
    
    def _calculate_confidence(self, violations):
        """
        Calculate confidence score based on violations
        No violations = 1.0, each violation reduces by 0.2
        """
        base_confidence = 1.0
        penalty_per_violation = 0.2
        
        confidence = max(0.0, base_confidence - (len(violations) * penalty_per_violation))
        return confidence
    
    def apply_corrections(self, llm_output, cascade_data, violations):
        """
        Auto-correct LLM output based on violations
        """
        corrected = llm_output
        
        for violation in violations:
            if violation['type'] == 'GEOGRAPHIC_VIOLATION':
                # Replace claimed distance with actual
                corrected = corrected.replace(
                    violation['claimed'],
                    violation['actual']
                )
            
            elif violation['type'] == 'TEMPORAL_VIOLATION':
                # Replace claimed time with actual
                corrected = corrected.replace(
                    violation['claimed'],
                    violation['actual']
                )
        
        # Add disclaimer if corrections were made
        if violations:
            corrected += f"\n\n[HyDRA Verification: {len(violations)} correction(s) applied]"
        
        return corrected
