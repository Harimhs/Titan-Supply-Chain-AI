# Research & Novel Contributions: The DCBA Algorithm

## 1. The Core Engineering Problem
[cite_start]While integrating multiple RAG approaches (GraphRAG, Vector, CRAG) provides better coverage, it introduces the **"Multi-RAG Context Budget Conflict"**[cite: 572].
* **The Conflict:** A single query might trigger:
    * GraphRAG retrieval (2,500 tokens)
    * Vector chunk retrieval (3,200 tokens)
    * Web search verification (1,800 tokens)
    * Conversation history (2,000 tokens)
* **Total:** ~9,500 tokens.
* [cite_start]**Constraint:** Standard LLM context windows (8k) lead to **Context Overflow**[cite: 575, 576]. [cite_start]Existing solutions (random truncation) cause information loss and hallucinations[cite: 578].

## 2. Novel Contribution: Dynamic Context Budget Allocation (DCBA)
[cite_start]TITAN implements a novel **Dynamic Context Budget Allocator (DCBA)**, an agentic system that optimizes token usage in real-time[cite: 587].

### Algorithm Methodology
1.  [cite_start]**Query Analysis Agent:** Classifies queries by "Complexity Score" (multi-hop depth) and "Entity Density" to predict the most effective retrieval architecture[cite: 590, 601].
2.  **State-Aware Context Management:** Maintains a persistent `StateGraph` of the conversation. [cite_start]If a user asks "What about Mumbai?", the system reuses cached entities from the previous turn rather than re-fetching, saving ~40% of tokens[cite: 618, 631, 632].
3.  [cite_start]**Intelligent Compression:** Instead of truncating text, DCBA uses "Protected Entity Extraction" to keep high-value nodes while compressing generic description text[cite: 718, 719].

## 3. Experimental Results
[cite_start]We evaluated TITAN against a baseline "Naive RAG" (equal allocation) across 500 supply chain disruption scenarios[cite: 733, 734].

| Metric | Baseline RAG | TITAN (DCBA) | Improvement |
| :--- | :--- | :--- | :--- |
| **Context Overflow Rate** | 47% of queries | **2%** of queries | [cite_start]**96% Reduction** [cite: 736] |
| **Hallucination Rate** | 18% | **5%** | [cite_start]**72% Reduction** [cite: 664] |
| **Avg Response Time** | 3.2s | **1.1s** | [cite_start]**66% Faster** [cite: 664] |
| **Cascade Prediction** | 41% accuracy | **94%** accuracy | [cite_start]**Tier-N Visibility** [cite: 496] |

## 4. Architectural Proof of Concept
TITAN demonstrates that **State-Aware Allocation** allows lightweight models (Llama 3 via Groq) to outperform larger models by ensuring the *right* context is present, rather than *more* context.