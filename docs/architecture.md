# TITAN System Architecture

## 1. High-Level Overview
TITAN operates on a **Hybrid Neuro-Symbolic Architecture**, combining the structured reasoning of Knowledge Graphs with the semantic understanding of Large Language Models (LLMs). Unlike traditional RAG systems that rely solely on vector similarity, TITAN grounds its generative responses in a mathematically rigorous graph topology.

## 2. Core Components

### A. The "Brain" (Orchestration Layer)
* **Role:** Central controller that parses user intent and routes queries.
* **Implementation:** `TitanBrain` class (Python).
* **Logic:**
    1.  Receives natural language query.
    2.  **Intent Classification:** Decides if the query requires Graph Data (spatial/structural), Vector Data (unstructured text), or both.
    3.  **Context Assembly:** Aggregates results into a prompt context window.
    4.  **Generation:** Sends enriched context to Groq (Llama 3) for the final answer.

### B. The Structured Core (Graph Database)
* **Tech:** Neo4j (AuraDB).
* **Role:** Stores the "Physical Reality" of the supply chain.
* **Why Graph?** Supply chains are inherently network-based. Relational databases (SQL) struggle with multi-hop queries like *"Find all warehouses connected to Factory A that are within 500km of a disaster."* Graph DBs handle this natively with $O(1)$ index-free adjacency.

### C. The Semantic Memory (Vector Database)
* **Tech:** ChromaDB.
* **Role:** Stores unstructured knowledge (Product manuals, risk reports, geopolitical news).
* **Mechanism:** Uses `all-MiniLM-L6-v2` embeddings to retrieve documents semantically related to the user's query, even if keywords don't match exactly.

### D. The Visualization Layer
* **Tech:** Three.js / Globe.gl.
* **Role:** Renders the graph topology in real-time 3D space.
* **Integration:** Fetches GeoJSON-like node data directly from the Python backend, bypassing the LLM for pure data visualization speed.

## 3. Data Flow Diagram
User Query 
  │
  ▼
[TitanBrain] ───▶ [Intent Classifier]
  │
  ├──▶ (If Spatial/Relational) ──▶ [Neo4j Cypher Query] ──▶ Returns Nodes/Edges
  │
  ├──▶ (If Semantic/Textual) ────▶ [ChromaDB Vector Search] ──▶ Returns Text Chunks
  │
  ▼
[Context Fusion Engine]
  │ (Combines Graph Facts + Vector Text)
  ▼
[Groq LLM Inference]
  │
  ▼
Final Response