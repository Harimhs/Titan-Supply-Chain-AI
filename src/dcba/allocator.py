from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from src.llm.gemini_client import GeminiClient
from src.utils.config import Config
from typing import Dict
import re

class DynamicBudgetAllocator:
    """
    DCBA: Dynamic Context Budget Allocator
    
    The Novel Algorithm that decides how to split limited context window
    across multiple RAG systems based on query complexity.
    """
    
    def __init__(self):
        self.llm_client = GeminiClient(temperature=0)  # Deterministic
        self.llm = self.llm_client.get_llm()
        self.total_budget = Config.MAX_CONTEXT_TOKENS
        
        # Pattern matching for fast classification (fallback)
        self.graph_keywords = ['impact', 'affect', 'cascade', 'ripple', 'supply chain', 
                               'downstream', 'upstream', 'path', 'route', 'dependency']
        self.vector_keywords = ['product', 'sku', 'inventory', 'stock', 'where is', 
                                'find', 'list', 'specifications']
        self.crag_keywords = ['current', 'latest', 'now', 'today', 'verify', 'check',
                              'real-time', 'live']

    def quick_classify(self, query: str) -> str:
        """
        Fast rule-based classification (no LLM call)
        Used as fallback if LLM is slow/unavailable
        """
        query_lower = query.lower()
        
        graph_score = sum(1 for kw in self.graph_keywords if kw in query_lower)
        vector_score = sum(1 for kw in self.vector_keywords if kw in query_lower)
        crag_score = sum(1 for kw in self.crag_keywords if kw in query_lower)
        
        scores = {'GraphRAG': graph_score, 'VectorRAG': vector_score, 'CRAG': crag_score}
        return max(scores, key=scores.get)

    def analyze_query_complexity(self, query: str, use_llm: bool = True) -> Dict:
        """
        PHASE 1: Predicts which RAG architecture is needed
        
        Returns: 
            {
                "complexity": 0.0-1.0,
                "primary_method": "GraphRAG" | "VectorRAG" | "CRAG",
                "reasoning": "explanation",
                "requires_multi_hop": bool
            }
        """
        if not use_llm:
            # Fast fallback
            method = self.quick_classify(query)
            return {
                "complexity": 0.6,
                "primary_method": method,
                "reasoning": "Rule-based classification",
                "requires_multi_hop": method == "GraphRAG"
            }
        
        parser = JsonOutputParser()
        prompt = PromptTemplate(
            template="""You are the Brain of TITAN Supply Chain AI.
Analyze this query to determine the optimal Retrieval Strategy.

Query: {query}

**Strategy Definitions:**
- **GraphRAG**: Use for "ripple effects", "impact analysis", "cascade failures", "path tracing", "X affects Y".
  Example: "How does Shanghai port closure affect Coimbatore warehouse?"
  
- **VectorRAG**: Use for "factual lookups", "product details", "inventory queries", "specifications".
  Example: "Where is iPhone 15 stocked?" or "What products are in Mumbai warehouse?"
  
- **CRAG**: Use for "real-time verification", "current events", "disaster confirmation", "live updates".
  Example: "Is there currently a typhoon in Taiwan?"

**Return JSON:**
{{
    "complexity": <float 0.0-1.0>,
    "primary_method": "GraphRAG" or "VectorRAG" or "CRAG",
    "reasoning": "brief explanation",
    "requires_multi_hop": <bool>
}}

Rules:
- Complexity 0.0-0.3: Simple lookup
- Complexity 0.4-0.7: Moderate reasoning
- Complexity 0.8-1.0: Deep multi-hop analysis
- Set requires_multi_hop=true if query needs 3+ hops in supply chain
""",
            input_variables=["query"]
        )
        
        chain = prompt | self.llm | parser
        
        try:
            result = chain.invoke({"query": query})
            print(f"🧠 Query Analysis: {result}")
            return result
        except Exception as e:
            print(f"⚠️ LLM Analysis Failed, using fallback: {e}")
            # Fallback to rule-based
            method = self.quick_classify(query)
            return {
                "complexity": 0.5,
                "primary_method": method,
                "reasoning": "Fallback classification",
                "requires_multi_hop": method == "GraphRAG"
            }

    def allocate_budget(self, analysis_result: Dict, history_len: int = 0) -> Dict:
        """
        PHASE 2: The DCBA Algorithm
        Allocates context tokens based on query prediction
        
        Args:
            analysis_result: Output from analyze_query_complexity()
            history_len: Number of previous conversation turns
            
        Returns:
            {
                'history': tokens for conversation history,
                'graph': tokens for GraphRAG,
                'vector': tokens for VectorRAG,
                'web': tokens for CRAG,
                'output': tokens reserved for LLM output
            }
        """
        budget = {}
        remaining = self.total_budget
        
        # 1. Reserve for Output (LLM needs space to respond)
        output_reserve = 1500  # Fixed reserve for response
        budget['output'] = output_reserve
        remaining -= output_reserve
        
        # 2. Reserve for History (Adaptive Compression)
        if history_len == 0:
            budget['history'] = 0
        elif history_len <= 3:
            budget['history'] = 300  # Recent context
        else:
            # Compress older history
            budget['history'] = min(800, 200 + history_len * 50)
        
        remaining -= budget['history']
        
        # 3. Main Allocation: THE DCBA ALGORITHM
        method = analysis_result.get('primary_method', 'VectorRAG')
        complexity = analysis_result.get('complexity', 0.5)
        multi_hop = analysis_result.get('requires_multi_hop', False)
        
        if method == "GraphRAG":
            # Complex multi-hop reasoning needs deep graph context
            if multi_hop or complexity > 0.7:
                # HIGH COMPLEXITY: Deep cascades
                budget['graph'] = int(remaining * 0.70)  # 70% to Graph
                budget['vector'] = int(remaining * 0.20) # 20% to Vector (context)
                budget['web'] = int(remaining * 0.10)    # 10% to CRAG (verify)
            else:
                # MEDIUM: Standard path finding
                budget['graph'] = int(remaining * 0.60)
                budget['vector'] = int(remaining * 0.25)
                budget['web'] = int(remaining * 0.15)
            
        elif method == "VectorRAG":
            # Factual lookups need precise text chunks
            if complexity < 0.4:
                # SIMPLE: Direct lookup
                budget['vector'] = int(remaining * 0.80)
                budget['graph'] = int(remaining * 0.10)
                budget['web'] = int(remaining * 0.10)
            else:
                # MODERATE: Multiple sources
                budget['vector'] = int(remaining * 0.65)
                budget['graph'] = int(remaining * 0.25)
                budget['web'] = int(remaining * 0.10)
            
        else:  # CRAG / Web Focus
            # Real-time verification heavy
            budget['web'] = int(remaining * 0.55)
            budget['vector'] = int(remaining * 0.30)
            budget['graph'] = int(remaining * 0.15)
        
        # 4. Ensure all budgets assigned
        total_allocated = sum([budget['graph'], budget['vector'], budget['web']])
        if total_allocated < remaining:
            # Add leftover to primary method
            budget[method.lower().replace('rag', '')] += (remaining - total_allocated)
        
        return budget
    
    def print_allocation(self, budget: Dict):
        """Pretty print budget allocation"""
        print("\n💰 DCBA Token Allocation:")
        total = sum(budget.values())
        for key, tokens in budget.items():
            pct = (tokens / total) * 100 if total > 0 else 0
            bar = "█" * int(pct / 2)
            print(f"   {key.upper():<10} : {tokens:>5} tokens [{bar:<50}] {pct:.1f}%")
        print(f"   {'TOTAL':<10} : {total:>5} tokens")

    def allocate(
    self, 
    query: str, 
    contexts: Dict[str, str],
    allocation: Dict[str, float] = None,
    budget: int = None
) -> Dict:
        """
        Wrapper for orchestrator compatibility
        
        Args:
            query: User query
            contexts: Dict of context sources {"disaster": "...", "graph": "...", "vector": "..."}
            allocation: Optional predefined allocation ratios
            budget: Optional custom budget (uses Config.MAX_CONTEXT_TOKENS if None)
        
        Returns:
            {
                "final_context": "combined optimized context",
                "compression_ratio": 0.65,
                "tokens_used": 5200
            }
        """
        if budget:
            self.total_budget = budget
        
        # Analyze query
        analysis = self.analyze_query_complexity(query, use_llm=False)
        
        # Get budget allocation
        budget_allocation = self.allocate_budget(analysis, history_len=0)
        
        # Apply context with token limits
        final_parts = []
        total_original_tokens = 0
        total_used_tokens = 0
        
        # Map context keys to budget keys
        context_to_budget = {
            "disaster": "web",  # Treat disaster as external/web data
            "graph": "graph",
            "vector": "vector"
        }
        
        for ctx_key, ctx_text in contexts.items():
            if not ctx_text:
                continue
            
            budget_key = context_to_budget.get(ctx_key, "vector")
            token_limit = budget_allocation.get(budget_key, 1000)
            
            # Estimate tokens (rough: 4 chars = 1 token)
            original_tokens = len(ctx_text) // 4
            total_original_tokens += original_tokens
            
            if original_tokens <= token_limit:
                # Fits within budget
                final_parts.append(f"### {ctx_key.upper()} CONTEXT:\n{ctx_text}\n")
                total_used_tokens += original_tokens
            else:
                # Truncate to budget
                char_limit = token_limit * 4
                truncated = ctx_text[:char_limit] + "...[truncated]"
                final_parts.append(f"### {ctx_key.upper()} CONTEXT:\n{truncated}\n")
                total_used_tokens += token_limit
        
        final_context = "\n".join(final_parts)
        
        compression_ratio = 1.0 - (total_used_tokens / max(total_original_tokens, 1))
        
        return {
            "final_context": final_context,
            "compression_ratio": compression_ratio,
            "tokens_used": total_used_tokens,
            "budget_allocation": budget_allocation
        }


# --- COMPREHENSIVE TESTS ---
if __name__ == "__main__":
    dcba = DynamicBudgetAllocator()
    
    test_queries = [
        "Where is iPhone 15 stocked in Mumbai?",  # VectorRAG
        "Taiwan earthquake destroyed TSMC factory. How does this impact Coimbatore warehouse?",  # GraphRAG
        "Is there a typhoon in Shanghai right now?",  # CRAG
        "Show me the supply chain path from China to USA"  # GraphRAG Multi-hop
    ]
    
    print("="*70)
    print("🧪 TESTING DCBA ALGORITHM")
    print("="*70)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*70}")
        print(f"TEST {i}: {query}")
        print(f"{'='*70}")
        
        # Analyze
        analysis = dcba.analyze_query_complexity(query, use_llm=False)  # Fast test
        print(f"\n📊 Analysis Result:")
        print(f"   Method: {analysis['primary_method']}")
        print(f"   Complexity: {analysis['complexity']}")
        print(f"   Multi-hop: {analysis.get('requires_multi_hop', False)}")
        
        # Allocate
        allocation = dcba.allocate_budget(analysis, history_len=2)
        dcba.print_allocation(allocation)
    
    print("\n" + "="*70)
    print("✅ DCBA Tests Complete!")
    print("="*70)
