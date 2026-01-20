#!/usr/bin/env python3
"""
Query Analyzer - FIXED VERSION
Returns keys that match allocator expectations
"""
import re

class QueryAnalyzer:
    """Analyze query characteristics for DCBA allocation"""
    
    def __init__(self):
        # All countries from data
        self.all_countries = [
            "China", "India", "Japan", "South Korea", "Singapore",
            "USA", "Canada", "Brazil", "Argentina",
            "Germany", "UK", "France", "Italy", "Poland", "Russia",
            "South Africa", "Egypt", "Australia"
        ]
        print("✅ Query Analyzer initialized")
    
    def analyze(self, query: str) -> dict:
        """
        Analyze query and return characteristics
        FIXED: Returns 'type' not 'query_type' to match allocator
        """
        # Calculate complexity
        complexity = self._calculate_complexity(query)
        
        # Determine query type (for DCBA allocator)
        query_type = self._determine_dcba_type(query)
        
        # Extract entities
        entities = self._extract_entities(query)
        
        # Check for temporal references
        is_temporal = self._has_temporal(query)
        
        return {
            "query": query,
            "complexity": complexity,
            "type": query_type,  # FIXED: Use 'type' not 'query_type'
            "entities": entities,
            "is_temporal": is_temporal,
            "word_count": len(query.split()),
            "has_negation": self._has_negation(query),
            "requires_graph": self._requires_graph(query),
            "requires_vector": self._requires_vector(query)
        }
    
    def _determine_dcba_type(self, query: str) -> str:
        """
        Determine DCBA query type for allocator
        
        Returns:
            'cascade_analysis', 'disaster_impact', 'product_search', 
            'inventory_check', or 'general'
        """
        query_lower = query.lower()
        
        # Cascade analysis
        if any(word in query_lower for word in ['cascade', 'downstream', 'upstream', 'impact chain']):
            return 'cascade_analysis'
        
        # Disaster impact
        if any(word in query_lower for word in ['disaster', 'earthquake', 'flood', 'typhoon', 'disruption']):
            return 'disaster_impact'
        
        # Product search
        if any(word in query_lower for word in ['product', 'find', 'search', 'where', 'manufactured']):
            return 'product_search'
        
        # Inventory check
        if any(word in query_lower for word in ['inventory', 'stock', 'warehouse', 'storage']):
            return 'inventory_check'
        
        # Default
        return 'general'
    
    def _calculate_complexity(self, query: str) -> str:
        """Calculate query complexity"""
        word_count = len(query.split())
        
        has_multiple_conditions = any(word in query.lower() for word in ['and', 'or', 'but', 'while'])
        has_comparison = any(word in query.lower() for word in ['compare', 'difference', 'versus', 'vs'])
        has_aggregation = any(word in query.lower() for word in ['total', 'average', 'sum', 'count'])
        
        if word_count > 15 or has_comparison or (has_multiple_conditions and has_aggregation):
            return 'complex'
        elif word_count > 7 or has_multiple_conditions or has_aggregation:
            return 'medium'
        else:
            return 'simple'
    
    def _extract_entities(self, query: str) -> dict:
        """Extract entities - FIXED PATTERN"""
        entities = {
            "facilities": [],
            "countries": [],
            "products": [],
            "disasters": []
        }
        
        # FIX: More flexible facility pattern
        # Matches: FACTORY_0001, FACTORY-0001, Factory 0001, etc.
        facility_pattern = r'(FACTORY|WAREHOUSE|PORT)[\s_-]?(\d{4})'
        matches = re.findall(facility_pattern, query, re.IGNORECASE)
        
        for match in matches:
            facility_type = match[0].upper()
            facility_num = match[1]
            # Format: FACTORY_0001
            entities["facilities"].append(f"{facility_type}_{facility_num}")
        
        # Extract product IDs
        product_pattern = r'\bP[1-5]\b'
        products = re.findall(product_pattern, query, re.IGNORECASE)
        entities["products"] = [p.upper() for p in products]
        
        # Extract countries
        for country in self.all_countries:
            if re.search(r'\b' + re.escape(country.lower()) + r'\b', query.lower()):
                entities["countries"].append(country)
        
        return entities

    
    def _requires_graph(self, query: str) -> bool:
        """Check if query needs GraphRAG"""
        graph_keywords = [
            'path', 'route', 'connection', 'relationship', 'network',
            'supply chain', 'cascade', 'downstream', 'upstream'
        ]
        return any(word in query.lower() for word in graph_keywords)
    
    def _requires_vector(self, query: str) -> bool:
        """Check if query needs VectorRAG"""
        vector_keywords = [
            'find', 'search', 'similar', 'like', 'about',
            'description', 'details', 'information'
        ]
        return any(word in query.lower() for word in vector_keywords)
    
    def _has_temporal(self, query: str) -> bool:
        """Check if query has temporal references"""
        temporal_words = [
            'when', 'time', 'date', 'year', 'month', 'day',
            'recent', 'latest', 'current', 'past', 'future'
        ]
        return any(word in query.lower() for word in temporal_words)
    
    def _has_negation(self, query: str) -> bool:
        """Check if query has negation"""
        negation_words = ['not', 'no', 'never', 'neither', 'without', 'except']
        return any(word in query.lower() for word in negation_words)
