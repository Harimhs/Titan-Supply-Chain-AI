#!/usr/bin/env python3
"""
Master Query Orchestrator - UNLEASHED VERSION 🚀
Routes queries to appropriate RAG/Analytics systems with HIGH DATA LIMITS
"""
import sys
from pathlib import Path
import re

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.rag.vector_rag import VectorRAG
from src.graph.neo4j_client import Neo4jClient
from src.analytics.risk_engine import RiskAssessmentEngine
from src.analytics.route_optimizer import RouteOptimizer
from src.rag.ml_predictor import DemandPredictor

class QueryOrchestrator:
    """Route and execute complex supply chain queries"""
    
    def __init__(self):
        """Initialize all components"""
        self.vector_rag = VectorRAG()
        self.neo4j = Neo4jClient()
        self.risk_engine = RiskAssessmentEngine()
        self.route_optimizer = RouteOptimizer()
        self.ml_predictor = DemandPredictor()
        
        self.all_countries = [
            "China", "India", "Japan", "South Korea", "Singapore",
            "USA", "Canada", "Brazil", "Argentina",
            "Germany", "UK", "France", "Italy", "Poland", "Russia",
            "South Africa", "Egypt", "Australia"
        ]
        
        self.product_base_demand = {
            "P1": 1000, "P2": 600, "P3": 800, "P4": 500, "P5": 1500
        }
        
        print("✅ Query Orchestrator initialized")
    
    def classify_query(self, query):
        """Classify query intent with robust detection"""
        query_lower = query.lower()
        entities = self._extract_entities(query)
        
        # Intent Classification Logic
        if any(word in query_lower for word in ['risk', 'danger', 'threat', 'vulnerable', 'assessment']):
            intent = "risk_assessment"
        elif any(word in query_lower for word in ['route', 'path', 'deliver', 'transport', 'ship', 'alternative']):
            intent = "route_optimization"
        elif any(word in query_lower for word in ['predict', 'forecast', 'demand', 'future']):
            intent = "ml_prediction"
        elif any(word in query_lower for word in ['disaster', 'earthquake', 'flood', 'typhoon', 'hurricane']):
            intent = "disaster_analysis"
        elif any(word in query_lower for word in ['factory', 'warehouse', 'port', 'facility', 'plant', 'capacity', 'list', 'show', 'how many']):
            intent = "facility_query"
        elif any(word in query_lower for word in ['product', 'electronics', 'automotive', 'pharmaceutical', 'textile', 'consumer', 'goods']):
            intent = "product_query"
        elif entities["countries"]:
            intent = "country_analysis"
        else:
            intent = "general_search"
        
        return {
            "intent": intent,
            "entities": entities,
            "original_query": query
        }
    
    def _extract_entities(self, query):
        """Extract entities"""
        entities = {
            "facilities": [],
            "countries": [],
            "products": [],
            "disasters": []
        }
        
        facility_pattern = r'(?:FACTORY|WAREHOUSE|PORT)_\d{4}'
        facilities = re.findall(facility_pattern, query, re.IGNORECASE)
        entities["facilities"] = [f.upper() for f in facilities]
        
        product_pattern = r'\bP[1-5]\b'
        products = re.findall(product_pattern, query, re.IGNORECASE)
        entities["products"] = [p.upper() for p in products]
        
        for country in self.all_countries:
            if re.search(r'\b' + re.escape(country.lower()) + r'\b', query.lower()):
                entities["countries"].append(country)
        
        return entities
    
    def execute_query(self, query):
        """Execute query using appropriate systems"""
        classification = self.classify_query(query)
        intent = classification["intent"]
        entities = classification["entities"]
        
        print(f"\n🔍 Query: {query}")
        print(f"📊 Intent: {intent}")
        print(f"🎯 Entities: {entities}\n")
        
        results = {
            "query": query,
            "intent": intent,
            "entities": entities,
            "data": {}
        }
        
        # Route to handler
        if intent == "risk_assessment":
            results["data"] = self._handle_risk_query(entities)
        elif intent == "route_optimization":
            results["data"] = self._handle_route_query(entities)
        elif intent == "ml_prediction":
            results["data"] = self._handle_prediction_query(entities)
        elif intent == "disaster_analysis":
            results["data"] = self._handle_disaster_query(entities, query)
        elif intent == "facility_query":
            results["data"] = self._handle_facility_query(entities, query)
        elif intent == "product_query":
            results["data"] = self._handle_product_query(entities, query)
        elif intent == "country_analysis":
            results["data"] = self._handle_country_query(entities)
        else:
            results["data"] = self._handle_general_search(query)
        
        return results

    # --- HANDLERS (UPDATED FOR DATA VOLUME) ---

    def _handle_risk_query(self, entities):
        results = {}
        if entities["facilities"]:
            results["facility_risk"] = self.risk_engine.assess_facility_risk(entities["facilities"][0])
        elif entities["countries"]:
            results["country_risk"] = self.risk_engine.assess_country_risk(entities["countries"][0])
        else:
            results["top_risks"] = self.risk_engine.get_highest_risk_facilities(limit=10) # INCREASED LIMIT
        return results

    def _handle_route_query(self, entities):
        results = {}
        if len(entities["facilities"]) >= 2:
            source, dest = entities["facilities"][0], entities["facilities"][1]
            results["routes"] = self.route_optimizer.find_alternative_routes(source, dest, max_routes=3)
            results["best_route"] = self.route_optimizer.recommend_best_route(source, dest, criteria="time")
        elif entities["facilities"]:
            results["diversification"] = self.route_optimizer.suggest_route_diversification(entities["facilities"][0])
        return results

    def _handle_prediction_query(self, entities):
        # (Same as before, logic was fine here)
        results = {}
        if not entities["products"]:
            # Basic inference
            q = self.classify_query.__self__.original_query.lower() if hasattr(self.classify_query, '__self__') else ""
            if "automotive" in q: entities["products"] = ["P2"]
            elif "electronics" in q: entities["products"] = ["P1"]
        
        if entities["products"] and entities["countries"]:
            pid, ctry = entities["products"][0], entities["countries"][0]
            # Mock historical for now to ensure it runs
            results["prediction"] = self.ml_predictor.predict(
                product_id=pid, country=ctry, country_strength=0.8, lag_1_demand=1000
            )
        else:
            results["error"] = "Please specify product and country."
        return results

    def _handle_disaster_query(self, entities, query):
        results = {}
        # UNLEASHED: Increase limits
        results["disasters"] = self.vector_rag.search_disasters(query, n_results=10)
        results["active_disasters"] = self.neo4j.get_active_disasters() # Gets all of them
        return results

    def _detect_facility_type(self, query):
        q = query.lower()
        if 'warehouse' in q: return 'warehouse'
        if 'port' in q: return 'port'
        return 'factory' # Default

    def _handle_facility_query(self, entities, query):
        """Handle facility queries with BROAD SEARCH support"""
        results = {}
        f_type = self._detect_facility_type(query)

        if entities["facilities"]:
            # Specific facility
            fid = entities["facilities"][0]
            results["facility"] = self.neo4j.run_query("MATCH (f {id: $id}) RETURN f", {"id": fid})
            results["supply_routes"] = self.neo4j.get_factory_supply_routes(fid)[:10]
        
        elif entities["countries"]:
            # Specific Country
            country = entities["countries"][0]
            if f_type == 'port':
                results["ports"] = self.neo4j.get_ports_by_country(country, limit=20)
            elif f_type == 'warehouse':
                results["warehouses"] = self.neo4j.get_warehouses_by_country(country, limit=20)
            else:
                results["factories"] = self.neo4j.get_factories_by_country(country, limit=20)
        
        else:
            # GLOBAL BROAD SEARCH (The missing piece!)
            # If no ID and no Country, fetch global stats from Graph
            if f_type == 'port':
                results["ports"] = self.neo4j.run_query("MATCH (p:Port) RETURN p LIMIT 20")
            elif f_type == 'warehouse':
                results["warehouses"] = self.neo4j.run_query("MATCH (w:Warehouse) RETURN w LIMIT 20")
            else:
                results["factories"] = self.neo4j.run_query("MATCH (f:Factory) RETURN f LIMIT 20")
                
            # Also run vector search as backup
            results["vector_search"] = self.vector_rag.search_factories(query, n_results=10)

        return results

    def _handle_product_query(self, entities, query):
        results = {}
        
        if entities["products"]:
            # Specific Product
            pid = entities["products"][0]
            results["factories"] = self.neo4j.get_factories_by_product(pid, limit=10)
            results["supply_network"] = self.neo4j.get_product_supply_network(pid, limit=20)
        
        else:
            # BROAD PRODUCT SEARCH
            # If user asks "products in China" but doesn't say P1
            if entities["countries"]:
                country = entities["countries"][0]
                # Custom query to find what products are made there
                q = """
                MATCH (f:Factory {country: $country}) 
                RETURN DISTINCT f.product_type as product, count(f) as factory_count
                """
                results["country_products"] = self.neo4j.run_query(q, {"country": country})
            
            # Vector fallback (INCREASED LIMIT)
            results["product_info"] = self.vector_rag.search_products(query, n_results=15)
            
        return results

    def _handle_country_query(self, entities):
        results = {}
        if entities["countries"]:
            country = entities["countries"][0]
            results["risk_assessment"] = self.risk_engine.assess_country_risk(country)
            results["supply_chain_stats"] = self.neo4j.get_country_supply_chain_stats(country)
        return results

    def _handle_general_search(self, query):
        results = {}
        # UNLEASHED: Increase limit to 10
        results["vector_search"] = self.vector_rag.search_all(query, n_results=10)
        return results

    def close(self):
        self.neo4j.close()
        self.risk_engine.close()
        self.route_optimizer.close()