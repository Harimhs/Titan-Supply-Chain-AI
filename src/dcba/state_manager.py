"""
State Manager: Track entities across conversation turns
"""

class StateManager:
    def __init__(self):
        self.state = {
            'entities': set(),
            'last_query_type': None,
            'context': {}
        }
    
    def update(self, query_analysis, results):
        """Update state with new query and results"""
        # Add entities from query
        for entity_type, entities in query_analysis['entities'].items():
            for entity in entities:
                self.state['entities'].add(entity)
        
        # Update query type
        self.state['last_query_type'] = query_analysis['type']
        
        # Store context
        if results:
            self.state['context']['last_results'] = results
    
    def get_active_entities(self):
        """Get all entities mentioned in conversation"""
        return list(self.state['entities'])
    
    def get_context(self):
        """Get conversation context"""
        return self.state['context']
    
    def clear(self):
        """Reset state"""
        self.state = {
            'entities': set(),
            'last_query_type': None,
            'context': {}
        }
