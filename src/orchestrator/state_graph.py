#!/usr/bin/env python3
"""
State Graph Orchestrator - Core Innovation
Multi-agent coordination with adaptive context management
"""

from typing import Dict, List, Optional, Any, Literal
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from datetime import datetime
from src.orchestrator.conversation_memory import ConversationMemory

from src.rag.graph_rag import GraphRAG
from src.rag.vector_rag import VectorRAG
from src.dcba.allocator import DynamicBudgetAllocator  # ✅ Fixed
from src.llm.groq_client import GroqLLM  # ✅ Fixed


# ============================================================================
# STATE DEFINITIONS
# ============================================================================

class StateType(Enum):
    """All possible states in the orchestration flow"""
    INIT = "init"
    QUERY_ANALYSIS = "query_analysis"
    DISASTER_CHECK = "disaster_check"
    CONTEXT_GATHERING = "context_gathering"
    DBCA_OPTIMIZATION = "dbca_optimization"
    LLM_GENERATION = "llm_generation"
    VALIDATION = "validation"
    COMPLETE = "complete"
    ERROR = "error"


class QueryIntent(Enum):
    """Classified query intents"""
    PRODUCT_SEARCH = "product_search"           # "Find iPhone suppliers"
    DISASTER_IMPACT = "disaster_impact"         # "Impact of Taiwan earthquake"
    ROUTE_OPTIMIZATION = "route_optimization"   # "Alternative routes to Mumbai"
    FACILITY_INFO = "facility_info"             # "Tell me about Shanghai port"
    COMPARISON = "comparison"                   # "Compare Port A vs Port B"
    GENERAL = "general"                         # Open-ended questions


@dataclass
class OrchestrationState:
    """
    State object passed through the graph
    Each node can read and modify this
    """
    # Input
    query: str
    user_constraints: Dict[str, Any] = field(default_factory=dict)
    
    # Classification
    intent: Optional[QueryIntent] = None
    entities: List[str] = field(default_factory=list)
    
    # Context
    graph_context: str = ""
    vector_context: str = ""
    disaster_context: str = ""
    
    # DBCA Optimization
    context_budget: int = 8000  # tokens
    optimized_context: str = ""
    compression_ratio: float = 0.0
    
    # LLM
    llm_response: str = ""
    
    # Metadata
    current_state: StateType = StateType.INIT
    confidence: float = 0.0
    sources: List[str] = field(default_factory=list)
    processing_time: Dict[str, float] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    
    # Transitions
    next_states: List[StateType] = field(default_factory=list)


# ============================================================================
# STATE GRAPH ORCHESTRATOR
# ============================================================================

class StateGraphOrchestrator:
    """
    Directed Acyclic Graph for query orchestration
    Innovation: Dynamic routing based on query intent + DBCA optimization
    """
    
    def __init__(self):
        self.graph_rag = GraphRAG()
        self.vector_rag = VectorRAG()
        self.dcba = DynamicBudgetAllocator()  # ✅ Fixed
        self.llm = GroqLLM()  # ✅ Fixed
        self.memory = ConversationMemory(max_recent_turns=5)
        
        # State transition rules (DAG)
        self.transitions = {
            StateType.INIT: [StateType.QUERY_ANALYSIS],
            StateType.QUERY_ANALYSIS: [StateType.DISASTER_CHECK, StateType.CONTEXT_GATHERING],
            StateType.DISASTER_CHECK: [StateType.CONTEXT_GATHERING],
            StateType.CONTEXT_GATHERING: [StateType.DBCA_OPTIMIZATION],
            StateType.DBCA_OPTIMIZATION: [StateType.LLM_GENERATION],
            StateType.LLM_GENERATION: [StateType.VALIDATION],
            StateType.VALIDATION: [StateType.COMPLETE, StateType.ERROR],
        }
    
    # ========================================================================
    # NODE 1: Query Analysis
    # ========================================================================
    
    async def node_query_analysis(self, state: OrchestrationState) -> OrchestrationState:
        """
        Classify query intent and extract entities
        Uses LLM for zero-shot classification
        """
        start_time = datetime.now()
        
        classification_prompt = f"""
Classify this supply chain query:

Query: "{state.query}"

Return JSON:
{{
    "intent": "product_search|disaster_impact|route_optimization|facility_info|comparison|general",
    "entities": ["entity1", "entity2"],
    "confidence": 0.95
}}

Examples:
- "Where can I source smartphones?" → product_search, entities: ["smartphone"]
- "Impact of Taiwan earthquake on supply chain?" → disaster_impact, entities: ["Taiwan", "earthquake"]
- "Alternative routes avoiding Shanghai" → route_optimization, entities: ["Shanghai"]
"""
        
        response = await self.llm.generate_async(classification_prompt, temperature=0.1)
        
        try:
            import json
            result = json.loads(response)
            state.intent = QueryIntent(result["intent"])
            state.entities = result["entities"]
            state.confidence = result["confidence"]
        except:
            # Fallback: keyword-based classification
            query_lower = state.query.lower()
            if any(w in query_lower for w in ["product", "sku", "supplier", "source"]):
                state.intent = QueryIntent.PRODUCT_SEARCH
            elif any(w in query_lower for w in ["disaster", "earthquake", "typhoon", "impact"]):
                state.intent = QueryIntent.DISASTER_IMPACT
            else:
                state.intent = QueryIntent.GENERAL
        
        state.processing_time["query_analysis"] = (datetime.now() - start_time).total_seconds()
        state.current_state = StateType.QUERY_ANALYSIS
        
        # Dynamic routing decision
        if state.intent == QueryIntent.DISASTER_IMPACT:
            state.next_states = [StateType.DISASTER_CHECK]
        else:
            state.next_states = [StateType.CONTEXT_GATHERING]
        
        return state
    
    # ========================================================================
    # NODE 2: Disaster Check
    # ========================================================================
    
    async def node_disaster_check(self, state: OrchestrationState) -> OrchestrationState:
        """
        Check for active disasters affecting query entities
        """
        start_time = datetime.now()
        
        disasters = self.graph_rag.get_active_disasters()
        
        if disasters:
            disaster_texts = []
            for d in disasters:
                disaster_texts.append(
                    f"- {d['location_name']}: {d['type']} "
                    f"(Severity: {d['severity']}, Recovery: {d.get('recovery_days', 'N/A')} days)"
                )
            state.disaster_context = "**Active Disasters:**\n" + "\n".join(disaster_texts)
            state.sources.append("graph:disasters")
        
        state.processing_time["disaster_check"] = (datetime.now() - start_time).total_seconds()
        state.current_state = StateType.DISASTER_CHECK
        state.next_states = [StateType.CONTEXT_GATHERING]
        
        return state
    
    # ========================================================================
    # NODE 3: Context Gathering (Multi-RAG)
    # ========================================================================
    
    async def node_context_gathering(self, state: OrchestrationState) -> OrchestrationState:
        """
        Parallel context gathering from multiple RAG systems
        Route based on query intent
        """
        start_time = datetime.now()
        
        # Route to appropriate RAG systems
        if state.intent == QueryIntent.PRODUCT_SEARCH:
            # VectorRAG only
            state.vector_context = self.vector_rag.get_context_for_query(state.query, max_tokens=3000)  # ✅ Fixed
            state.sources.append("vector:products")
        
        elif state.intent == QueryIntent.DISASTER_IMPACT:
            # GraphRAG for supply chain impact
            state.graph_context = self.graph_rag.generate_context(state.query)
            state.sources.append("graph:supply_chain")
        
        elif state.intent == QueryIntent.ROUTE_OPTIMIZATION:
            # GraphRAG for routes + VectorRAG for facilities
            state.graph_context = self.graph_rag.generate_context(state.query)
            state.sources.append("graph:routes")
        
        else:
            # Use both for general queries
            state.graph_context = self.graph_rag.generate_context(state.query)
            state.vector_context = self.vector_rag.get_context_for_query(state.query, max_tokens=2000)  # ✅ Fixed
            state.sources.extend(["graph:supply_chain", "vector:products"])
        
        state.processing_time["context_gathering"] = (datetime.now() - start_time).total_seconds()
        state.current_state = StateType.CONTEXT_GATHERING
        state.next_states = [StateType.DBCA_OPTIMIZATION]
        
        return state

    
    # ========================================================================
    # NODE 4: DBCA Optimization
    # ========================================================================
    
    async def node_dbca_optimization(self, state: OrchestrationState) -> OrchestrationState:
        """
        Dynamic Context Budget Allocation
        Core Innovation: Compress context intelligently
        """
        start_time = datetime.now()
        
        # Combine all contexts
        raw_contexts = {
            "disaster": state.disaster_context,
            "graph": state.graph_context,
            "vector": state.vector_context,
            "history": self.memory.get_context_for_llm()  # ✅ NEW - Add conversation history
        }
        
        # DBCA allocation based on query intent
        if state.intent == QueryIntent.DISASTER_IMPACT:
            allocation = {"disaster": 0.4, "graph": 0.5, "vector": 0.1}
        elif state.intent == QueryIntent.PRODUCT_SEARCH:
            allocation = {"disaster": 0.0, "graph": 0.2, "vector": 0.8}
        else:
            allocation = {"disaster": 0.2, "graph": 0.5, "vector": 0.3}
        
        # Optimize context
        optimized = self.dcba.allocate(
            query=state.query,
            contexts=raw_contexts,
            allocation=allocation,
            budget=state.context_budget
        )
        
        state.optimized_context = optimized["final_context"]
        state.compression_ratio = optimized.get("compression_ratio", 0.0)
        
        state.processing_time["dbca_optimization"] = (datetime.now() - start_time).total_seconds()
        state.current_state = StateType.DBCA_OPTIMIZATION
        state.next_states = [StateType.LLM_GENERATION]
        
        return state

    
    # ========================================================================
    # NODE 5: LLM Generation
    # ========================================================================
    
    async def node_llm_generation(self, state: OrchestrationState) -> OrchestrationState:
        """
        Generate final response with LLM
        """
        start_time = datetime.now()
        
        prompt = f"""
    You are TITAN, an expert supply chain analyst. Answer the user's question using the provided context.

    Context:
    {state.optimized_context}

    Question: {state.query}

    INSTRUCTIONS:
    1. Answer directly using FACTS from the context
    2. If context has numbers/statistics, USE THEM (don't say "information not available")
    3. If context mentions facilities/counts, LIST THEM
    4. Cite sources like [GraphRAG] or [VectorRAG]
    5. Be specific - use actual numbers, names, locations from context
    6. If truly no relevant info, then say "Information not available"

    Answer (be helpful and use the data provided):
    """
        
        state.llm_response = await self.llm.generate_async(prompt, temperature=0.3)
        
        state.processing_time["llm_generation"] = (datetime.now() - start_time).total_seconds()
        state.current_state = StateType.LLM_GENERATION
        state.next_states = [StateType.VALIDATION]
        
        return state

    
    # ========================================================================
    # NODE 6: Validation
    # ========================================================================
    
    async def node_validation(self, state: OrchestrationState) -> OrchestrationState:
        """
        Validate response quality
        """
        start_time = datetime.now()
        
        # Simple validation checks
        response_length = len(state.llm_response.split())
        
        if response_length < 10:
            state.errors.append("Response too short")
            state.next_states = [StateType.ERROR]
        elif "I don't know" in state.llm_response and len(state.sources) > 0:
            state.errors.append("Hallucination detected: sources available but not used")
            state.next_states = [StateType.ERROR]
        else:
            state.next_states = [StateType.COMPLETE]
        
        state.processing_time["validation"] = (datetime.now() - start_time).total_seconds()
        state.current_state = StateType.VALIDATION
        
        return state
    
    # ========================================================================
    # ORCHESTRATION LOOP
    # ========================================================================
    
    async def run(self, query: str, constraints: Dict = None) -> Dict[str, Any]:
        """
        Execute state graph for a query
        Returns complete orchestration result
        """
        # Add user query to memory
        self.memory.add_message("user", query)  # ✅ NEW
        
        state = OrchestrationState(
            query=query,
            user_constraints=constraints or {}
        )
        
        total_start = datetime.now()
        
        # State machine execution
        node_sequence = []
        
        while state.current_state != StateType.COMPLETE and state.current_state != StateType.ERROR:
            node_sequence.append(state.current_state.value)
            
            # Execute current node
            if state.current_state == StateType.INIT:
                state.next_states = [StateType.QUERY_ANALYSIS]
            
            elif state.current_state == StateType.QUERY_ANALYSIS:
                state = await self.node_query_analysis(state)
            
            elif state.current_state == StateType.DISASTER_CHECK:
                state = await self.node_disaster_check(state)
            
            elif state.current_state == StateType.CONTEXT_GATHERING:
                state = await self.node_context_gathering(state)
            
            elif state.current_state == StateType.DBCA_OPTIMIZATION:
                state = await self.node_dbca_optimization(state)
            
            elif state.current_state == StateType.LLM_GENERATION:
                state = await self.node_llm_generation(state)
            
            elif state.current_state == StateType.VALIDATION:
                state = await self.node_validation(state)
            
            # Transition to next state
            if state.next_states:
                state.current_state = state.next_states[0]
            else:
                break
            
            # Prevent infinite loops
            if len(node_sequence) > 20:
                state.errors.append("Max iterations exceeded")
                state.current_state = StateType.ERROR
                break
        
        total_time = (datetime.now() - total_start).total_seconds()
        
        # Add assistant response to memory
        self.memory.add_message("assistant", state.llm_response, metadata={  # ✅ NEW
            "intent": state.intent.value if state.intent else "unknown",
            "processing_time": total_time
        })
        
        # Build result
        return {
            "answer": state.llm_response,
            "intent": state.intent.value if state.intent else "unknown",
            "entities": state.entities,
            "sources": state.sources,
            "confidence": state.confidence,
            "compression_ratio": state.compression_ratio,
            "node_sequence": node_sequence,
            "processing_time": {
                **state.processing_time,
                "total": total_time
            },
            "context_used": {
                "disaster": len(state.disaster_context),
                "graph": len(state.graph_context),
                "vector": len(state.vector_context),
                "optimized": len(state.optimized_context)
            },
            "conversation_history": self.memory.get_last_n_messages(3),  # ✅ NEW
            "errors": state.errors
        }



# ============================================================================
# USAGE EXAMPLE
# ============================================================================

async def test_orchestrator():
    """Test the state graph orchestrator"""
    orchestrator = StateGraphOrchestrator()
    
    queries = [
        "What's the impact of Taiwan earthquake on electronics supply chain?",
        "Find me alternative suppliers for smartphones",
        "Show me chokepoints in Asia-Pacific region"
    ]
    
    for query in queries:
        print(f"\n{'='*70}")
        print(f"Query: {query}")
        print('='*70)
        
        result = await orchestrator.run(query)
        
        print(f"\n🎯 Intent: {result['intent']}")
        print(f"📊 Node Sequence: {' → '.join(result['node_sequence'])}")
        print(f"⏱️  Total Time: {result['processing_time']['total']:.2f}s")
        print(f"🗜️  Compression: {result['compression_ratio']:.1%}")
        print(f"\n💬 Answer:\n{result['answer'][:500]}...")


if __name__ == "__main__":
    asyncio.run(test_orchestrator())
