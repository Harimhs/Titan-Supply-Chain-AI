"""
DCBA: Dynamic Context Budget Allocator
THE NOVEL CONTRIBUTION - This is what makes TITAN unique!
"""

class DynamicContextBudgetAllocator:
    def __init__(self, max_budget=8000):  # tokens
        self.max_budget = max_budget
    
    def allocate(self, query_analysis, state):
        """
        Allocate context budget dynamically based on query type and state
        
        Returns: {
            'graph_rag': 5600,  # 70% for complex multi-hop
            'vector_rag': 1600, # 20% for semantic search
            'crag': 800         # 10% for verification
        }
        """
        complexity = query_analysis['complexity']
        query_type = query_analysis['type']
        
        # Base allocation
        allocation = {
            'graph_rag': 0,
            'vector_rag': 0,
            'crag': 0,
            'history': 500  # Reserve for conversation history
        }
        
        available_budget = self.max_budget - allocation['history']
        
        # ALLOCATION LOGIC (Based on query type and complexity)
        if query_type == 'cascade_analysis':
            # Complex multi-hop → prioritize GraphRAG
            allocation['graph_rag'] = int(available_budget * 0.70)  # 70%
            allocation['vector_rag'] = int(available_budget * 0.20) # 20%
            allocation['crag'] = int(available_budget * 0.10)       # 10%
        
        elif query_type == 'disaster_impact':
            # Spatial + cascade → GraphRAG + VectorRAG balanced
            allocation['graph_rag'] = int(available_budget * 0.55)  # 55%
            allocation['vector_rag'] = int(available_budget * 0.30) # 30%
            allocation['crag'] = int(available_budget * 0.15)       # 15%
        
        elif query_type == 'product_search':
            # Semantic search → prioritize VectorRAG
            allocation['graph_rag'] = int(available_budget * 0.20)  # 20%
            allocation['vector_rag'] = int(available_budget * 0.60) # 60%
            allocation['crag'] = int(available_budget * 0.20)       # 20%
        
        elif query_type == 'inventory_check':
            # Simple lookup → balanced
            allocation['graph_rag'] = int(available_budget * 0.40)  # 40%
            allocation['vector_rag'] = int(available_budget * 0.40) # 40%
            allocation['crag'] = int(available_budget * 0.20)       # 20%
        
        else:  # general
            # Even split
            allocation['graph_rag'] = int(available_budget * 0.33)
            allocation['vector_rag'] = int(available_budget * 0.33)
            allocation['crag'] = int(available_budget * 0.34)
        
        # Adjust based on complexity
        if complexity == 'complex':
            # Give more to GraphRAG for complex queries
            shift = int(allocation['vector_rag'] * 0.2)
            allocation['graph_rag'] += shift
            allocation['vector_rag'] -= shift
        
        return allocation
    
    def get_allocation_summary(self, allocation):
        """Get human-readable summary"""
        total = sum(allocation.values())
        return {
            k: f"{v} tokens ({v/total*100:.1f}%)"
            for k, v in allocation.items()
        }
