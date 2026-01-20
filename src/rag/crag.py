#!/usr/bin/env python3
"""
CRAG: Corrective Retrieval Augmented Generation
Validates RAG results and detects hallucinations
"""

class CRAG:
    """
    CRAG: Cross-validate Graph + Vector results
    """
    
    def __init__(self, graph_rag, vector_rag):
        self.graph_rag = graph_rag
        self.vector_rag = vector_rag
    
    def evaluate_confidence(self, query, graph_results, vector_results):
        """
        Evaluate confidence in RAG results
        
        Returns: 'high', 'medium', 'low'
        """
        # FIXED: Handle None and different result types
        if not graph_results and not vector_results:
            return 'low'
        
        if graph_results and not vector_results:
            return 'medium'
        
        if vector_results and not graph_results:
            # FIXED: Check if vector_results is dict or list
            if isinstance(vector_results, dict):
                # It's a dict with collections
                total_results = sum(len(v) if isinstance(v, list) else 0 for v in vector_results.values())
                return 'medium' if total_results > 0 else 'low'
            elif isinstance(vector_results, list):
                # It's a list of results
                if len(vector_results) == 0:
                    return 'low'
                avg_distance = sum(r.get('distance', 1.0) if isinstance(r, dict) else 1.0 for r in vector_results) / len(vector_results)
                return 'high' if avg_distance < 0.5 else 'medium'
            else:
                return 'low'
        
        # Both have results - high confidence
        return 'high'
    
    def verify_with_graph(self, vector_result):
        """
        Verify a vector result against graph database
        Prevents hallucinations
        """
        # Extract entity IDs from vector result
        entity_id = vector_result.get('metadata', {}).get('id')
        
        if not entity_id:
            return False
        
        # Verify entity exists in graph
        graph_entity = self.graph_rag.get_node_by_id(entity_id)
        return graph_entity is not None
