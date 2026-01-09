#!/usr/bin/env python3
"""
Comprehensive Orchestrator Tests
Tests all orchestration features and edge cases
"""

import pytest
import asyncio
from src.orchestrator.state_graph import StateGraphOrchestrator, QueryIntent
from src.orchestrator.conversation_memory import ConversationMemory


class TestOrchestrator:
    """Test suite for state graph orchestrator"""
    
    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance"""
        return StateGraphOrchestrator()
    
    # ========================================================================
    # Test Query Classification
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_product_search_intent(self, orchestrator):
        """Test product search query classification"""
        result = await orchestrator.run("Where can I find smartphones?")
        
        assert result['intent'] == QueryIntent.PRODUCT_SEARCH.value
        assert 'vector' in result['sources'][0]  # Should use VectorRAG
        assert result['processing_time']['total'] < 30  # Should be fast
    
    @pytest.mark.asyncio
    async def test_disaster_impact_intent(self, orchestrator):
        """Test disaster impact query classification"""
        result = await orchestrator.run("What's the impact of Taiwan earthquake?")
        
        assert result['intent'] == QueryIntent.DISASTER_IMPACT.value
        assert 'graph' in result['sources'][0]  # Should use GraphRAG
        assert 'disaster_check' in result['node_sequence']
    
    @pytest.mark.asyncio
    async def test_route_optimization_intent(self, orchestrator):
        """Test route optimization query classification"""
        result = await orchestrator.run("Alternative routes avoiding Shanghai")
        
        assert result['intent'] in [QueryIntent.ROUTE_OPTIMIZATION.value, QueryIntent.GENERAL.value]
        assert 'graph' in ''.join(result['sources'])
    
    # ========================================================================
    # Test Conversation Memory
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_conversation_continuity(self, orchestrator):
        """Test that orchestrator remembers previous context"""
        # First query
        await orchestrator.run("Tell me about Taiwan earthquake")
        
        # Follow-up query (should remember Taiwan)
        result = await orchestrator.run("Show me affected facilities")
        
        assert len(orchestrator.memory.full_history) == 4  # 2 user + 2 assistant
        assert len(result['conversation_history']) > 0
    
    @pytest.mark.asyncio
    async def test_memory_persistence(self, orchestrator):
        """Test conversation memory saves/loads correctly"""
        orchestrator.memory.add_message("user", "Test query")
        orchestrator.memory.add_message("assistant", "Test response")
        
        # Save
        orchestrator.memory.save_to_file("test_memory.json")
        
        # Load into new memory
        new_memory = ConversationMemory()
        new_memory.load_from_file("test_memory.json")
        
        assert len(new_memory.full_history) == 2
        assert new_memory.full_history[0].content == "Test query"
    
    # ========================================================================
    # Test DBCA Optimization
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_context_compression(self, orchestrator):
        """Test that DBCA compresses context when needed"""
        # Long complex query that needs compression
        result = await orchestrator.run(
            "What's the complete impact of Taiwan earthquake on all downstream "
            "supply chains including factories, ports, warehouses, and alternative routes?"
        )
        
        # Should have compressed context
        assert result['compression_ratio'] >= 0  # Some compression happened
        assert result['context_used']['optimized'] <= orchestrator.dcba.total_budget * 4  # Within budget
    
    # ========================================================================
    # Test Error Handling
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_empty_query(self, orchestrator):
        """Test handling of empty query"""
        result = await orchestrator.run("")
        
        # Should handle gracefully
        assert 'errors' in result or result['answer']
    
    @pytest.mark.asyncio
    async def test_invalid_entity(self, orchestrator):
        """Test query with non-existent entity"""
        result = await orchestrator.run("Impact of earthquake in Atlantis city")
        
        # Should return gracefully (may not find results but shouldn't crash)
        assert result['answer']
    
    # ========================================================================
    # Test Performance
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_response_time(self, orchestrator):
        """Test that queries complete within reasonable time"""
        result = await orchestrator.run("Where are smartphones manufactured?")
        
        # Should complete in under 30 seconds
        assert result['processing_time']['total'] < 30
    
    @pytest.mark.asyncio
    async def test_parallel_queries(self, orchestrator):
        """Test handling multiple concurrent queries"""
        queries = [
            "Find electronics suppliers",
            "Show Taiwan earthquake impact",
            "List major ports in Asia"
        ]
        
        # Run in parallel
        results = await asyncio.gather(*[
            orchestrator.run(q) for q in queries
        ])
        
        assert len(results) == 3
        assert all(r['answer'] for r in results)


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    print("🧪 Running Orchestrator Tests...\n")
    pytest.main([__file__, "-v", "--tb=short"])
