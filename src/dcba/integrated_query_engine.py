#!/usr/bin/env python3
"""
Integrated Query Engine - CLEAN WORKING VERSION
DCBA + Analytics Integration
"""
from src.dcba.query_analyzer import QueryAnalyzer
from src.dcba.state_manager import StateManager
from src.dcba.allocator import DynamicContextBudgetAllocator
from src.rag.graph_rag import GraphRAG
from src.rag.vector_rag import VectorRAG
from src.rag.crag import CRAG
from src.rag.rag_cache import RAGCache
try:
    from src.analytics.risk_engine_adapter import RiskEngineAdapter as RiskAssessmentEngine
except ImportError:
    from src.analytics.risk_engine import RiskAssessmentEngine

from src.analytics.route_optimizer import RouteOptimizer
from src.rag.ml_predictor import DemandPredictor
from src.graph.neo4j_client import Neo4jClient

class IntegratedQueryEngine:
    """DCBA Query Engine + Analytics"""
    
    def __init__(self):
        # Core DCBA
        self.analyzer = QueryAnalyzer()
        self.state = StateManager()
        self.allocator = DynamicContextBudgetAllocator()
        self.cache = RAGCache()
        
        # RAG systems
        self.graph_rag = GraphRAG()
        self.vector_rag = VectorRAG()
        self.crag = CRAG(self.graph_rag, self.vector_rag)
        
        # Analytics
        self.risk_engine = RiskAssessmentEngine()
        self.route_optimizer = RouteOptimizer()
        self.ml_predictor = DemandPredictor()
        self.neo4j = Neo4jClient()
        
        print("✅ Integrated Query Engine initialized (DCBA + Analytics)")
    
    def query(self, user_query: str) -> dict:
        """Main query execution"""
        # Check cache
        cache_key = f"query:{user_query}"
        cached = self.cache.get(cache_key)
        if cached:
            cached['from_cache'] = True
            return cached
        
        # Analyze query
        analysis = self.analyzer.analyze(user_query)
        
        # Check if analytics query
        analytics_type = self._detect_analytics(user_query, analysis)
        
        if analytics_type:
            result = self._handle_analytics(user_query, analytics_type, analysis)
        else:
            result = self._handle_dcba_query(user_query, analysis)
        
        # Cache and return
        self.cache.set(cache_key, result)
        return result
    
    def _detect_analytics(self, query: str, analysis: dict) -> str:
        """Detect analytics query type"""
        query_lower = query.lower()
        entities = analysis.get('entities', {})
        
        # Risk
        if any(w in query_lower for w in ['risk', 'vulnerable', 'threat', 'danger', 'assessment']):
            return 'risk'
        
        # Route
        if any(w in query_lower for w in ['route', 'path', 'deliver', 'transport', 'alternative']):
            return 'route'
        
        # Prediction
        if any(w in query_lower for w in ['predict', 'forecast', 'demand', 'future']):
            return 'prediction'
        
        # Country analysis
        if entities.get('countries') and any(w in query_lower for w in ['analyze', 'analysis', 'overview']):
            return 'country_analysis'
        
        # Facility search
        if any(w in query_lower for w in ['show', 'list', 'display']) and any(w in query_lower for w in ['factories', 'warehouses', 'ports']):
            return 'facility_search'
        
        # Product location
        if 'where' in query_lower and entities.get('products'):
            return 'product_location'
        
        return None
    
    def _handle_analytics(self, query: str, analytics_type: str, analysis: dict):
        """Handle analytics queries"""
        entities = analysis.get('entities', {})
        
        try:
            if analytics_type == 'risk':
                results = self._handle_risk(entities)
            elif analytics_type == 'route':
                results = self._handle_route(entities)
            elif analytics_type == 'prediction':
                results = self._handle_prediction(query, entities)
            elif analytics_type == 'country_analysis':
                results = self._handle_country_analysis(entities)
            elif analytics_type == 'facility_search':
                results = self._handle_facility_search(query, entities)
            elif analytics_type == 'product_location':
                results = self._handle_product_location(entities)
            else:
                results = {'error': 'Unknown analytics type'}
            
            return {
                'answer': self._format_analytics_answer(results, analytics_type),
                'analytics_type': analytics_type,
                'analysis': analysis,
                'results': results,
                'from_cache': False
            }
        except Exception as e:
            return {
                'answer': f"Error: {str(e)}",
                'analytics_type': analytics_type,
                'error': str(e),
                'from_cache': False
            }
    
    def _handle_risk(self, entities: dict):
        """Risk assessment"""
        if entities.get('facilities'):
            return {'facility_risk': self.risk_engine.assess_facility_risk(entities['facilities'][0])}
        elif entities.get('countries'):
            return {'country_risk': self.risk_engine.assess_country_risk(entities['countries'][0])}
        else:
            return {'top_risks': self.risk_engine.get_highest_risk_facilities(5)}
    
    def _handle_route(self, entities: dict):
        """Route optimization - SAFER VERSION"""
        facilities = entities.get('facilities', [])
        
        if len(facilities) < 2:
            return {'error': 'Specify 2 facility IDs (e.g., FACTORY_0001 to WAREHOUSE_0010)'}
        
        source = facilities[0]
        target = facilities[1]
        
        print(f"🔍 Finding routes: {source} → {target}")
        
        try:
            # TEMPORARY FIX: Use simple path finding
            query = """
            MATCH path = shortestPath((source {id: $source})-[:SUPPLIES_TO*1..4]->(target {id: $target}))
            RETURN 
                [node in nodes(path) | node.id] as nodes,
                [node in nodes(path) | node.name] as names,
                reduce(dist = 0, rel in relationships(path) | dist + rel.distance_km) as distance,
                reduce(time = 0, rel in relationships(path) | time + rel.time_days) as time
            LIMIT 10
            """
            
            with self.neo4j.driver.session() as session:
                result = session.run(query, source=source, target=target)
                records = list(result)
                
                if not records:
                    return {'error': f'No routes found between {source} and {target}'}
                
                routes = []
                for i, record in enumerate(records, 1):
                    routes.append({
                        'route_number': i,
                        'route_type': 'Direct' if len(record['nodes']) == 2 else 'Multi-hop',
                        'nodes': record['nodes'],
                        'node_names': record['names'],
                        'total_distance_km': record['distance'],
                        'estimated_time_days': record['time']
                    })
                
                best = routes[0] if routes else None
                if best:
                    best['recommendation_reason'] = 'Shortest path'
                
                return {'routes': routes, 'best_route': best}
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'error': f'Route error: {str(e)}'}

        
    def _handle_prediction(self, query: str, entities: dict):
        """ML prediction"""
        products = entities.get('products', [])
        countries = entities.get('countries', [])
        
        # Infer product
        if not products:
            q = query.lower()
            if 'automotive' in q: products = ['P2']
            elif 'pharma' in q: products = ['P3']
            elif 'textile' in q: products = ['P4']
            elif 'consumer' in q: products = ['P5']
            elif 'electronic' in q: products = ['P1']
        
        if products and countries:
            hist = self._get_historical_demand(products[0], countries[0])
            stability = self.risk_engine._base_country_stability.get(countries[0], 0.5)
            
            prediction = self.ml_predictor.predict(
                product_id=products[0],
                country=countries[0],
                country_strength=stability * 1.2,
                lag_1_demand=hist['lag_1_demand'],
                lag_2_demand=hist['lag_2_demand'],
                avg_demand=hist['avg_demand']
            )
            prediction['historical_context'] = hist
            return {'prediction': prediction}
        else:
            return {'error': 'Specify product (P1-P5) and country'}
    
    def _handle_country_analysis(self, entities: dict):
        """Country analysis"""
        if entities.get('countries'):
            country = entities['countries'][0]
            risk = self.risk_engine.assess_country_risk(country)
            
            stats_query = """
            MATCH (f:Factory {country: $country})
            OPTIONAL MATCH (f)-[r:SUPPLIES_TO]->()
            RETURN count(DISTINCT f) as num_factories, count(r) as num_routes, sum(f.capacity) as total_capacity
            """
            stats = self.neo4j.run_query(stats_query, {"country": country})
            
            return {
                'country': country,
                'risk_assessment': risk,
                'supply_chain_stats': stats[0] if stats else {}
            }
        return {'error': 'No country specified'}
    
    def _handle_facility_search(self, query: str, entities: dict):
        """Facility search"""
        q = query.lower()
        if entities.get('countries'):
            country = entities['countries'][0]
            
            if 'warehouse' in q:
                facilities = self.neo4j.get_warehouses_by_country(country, 20)
                ftype = 'warehouses'
            elif 'port' in q:
                facilities = self.neo4j.get_ports_by_country(country, 20)
                ftype = 'ports'
            else:
                facilities = self.neo4j.get_factories_by_country(country, 20)
                ftype = 'factories'
            
            return {'facility_type': ftype, 'country': country, 'facilities': facilities}
        return {'error': 'No country specified'}
    
    def _handle_product_location(self, entities: dict):
        """Product location"""
        if entities.get('products'):
            product_id = entities['products'][0]
            factories = self.neo4j.get_factories_by_product(product_id, 10)
            
            countries = {}
            for f in factories:
                country = f['f']['country']
                countries[country] = countries.get(country, 0) + 1
            
            return {'product_id': product_id, 'factories': factories, 'countries': countries}
        return {'error': 'No product specified'}
    
    def _get_historical_demand(self, product_id, country):
        """Get historical demand"""
        query = """
        MATCH (f:Factory {product_type: $product_id, country: $country})
        RETURN f.capacity as capacity, count(f) as num_factories
        """
        results = self.neo4j.run_query(query, {"product_id": product_id, "country": country})
        
        if results and results[0]['num_factories'] > 0:
            total = results[0]['capacity'] * results[0]['num_factories']
            demand = int(total * 0.7)
            return {
                "lag_1_demand": demand,
                "lag_2_demand": int(demand * 0.95),
                "avg_demand": int(demand * 0.98)
            }
        else:
            base = {"P1": 1000, "P2": 600, "P3": 800, "P4": 500, "P5": 1500}.get(product_id, 800)
            return {
                "lag_1_demand": base,
                "lag_2_demand": int(base * 0.95),
                "avg_demand": int(base * 0.98)
            }
    
    def _format_analytics_answer(self, results, analytics_type):
        """Format analytics answer"""
        if 'error' in results:
            return results['error']
        
        if analytics_type == 'risk':
            if 'facility_risk' in results:
                r = results['facility_risk']
                return f"{r['name']}: {r['risk_level']} risk ({r['overall_risk_score']})"
            elif 'country_risk' in results:
                r = results['country_risk']
                return f"{r['country']}: {r['total_facilities']} facilities, avg risk {r['average_risk_score']}"
        
        elif analytics_type == 'route':
            if 'routes' in results:
                return f"Found {len(results['routes'])} alternative routes"
        
        elif analytics_type == 'prediction':
            if 'prediction' in results:
                p = results['prediction']
                return f"Predicted {p['predicted_demand']:,} units for {p['product_id']} in {p['country']}"
        
        elif analytics_type == 'country_analysis':
            stats = results.get('supply_chain_stats', {})
            return f"{results.get('country')}: {stats.get('num_factories', 0)} factories, {stats.get('num_routes', 0)} routes"
        
        elif analytics_type == 'facility_search':
            count = len(results.get('facilities', []))
            return f"Found {count} {results.get('facility_type')} in {results.get('country')}"
        
        elif analytics_type == 'product_location':
            countries = results.get('countries', {})
            return f"{results.get('product_id')} manufactured in {len(countries)} countries: {', '.join(countries.keys())}"
        
        return "Complete"
    
    def _handle_dcba_query(self, user_query: str, analysis: dict):
        """Original DCBA handling"""
        allocation = self.allocator.allocate(analysis, self.state.get_context())
        
        graph_results = None
        vector_results = None
        answer = "No results found"
        
        try:
            query_type = analysis['type']
            
            if query_type == 'cascade_analysis':
                entities = analysis.get('entities', {})
                facilities = entities.get('facilities', [])
                if len(facilities) >= 1:
                    source_id = facilities[0]
                    target_id = facilities[1] if len(facilities) > 1 else "WH-000001"
                    graph_results = self.graph_rag.get_cascade_path(source_id, target_id)
                    if graph_results:
                        answer = f"Cascade path: {graph_results['hops']} hops, {graph_results['total_distance_km']:.0f} km"
            
            elif query_type == 'product_search':
                vector_results = self.vector_rag.search_products(user_query, n_results=10)
                if vector_results:
                    answer = f"Found {len(vector_results)} products"
            
            else:
                if analysis.get('requires_vector', True):
                    vector_results = self.vector_rag.search_all(user_query, n_results=5 )
                    if vector_results:
                        answer = f"Found {sum(len(v) for v in vector_results.values())} results"
        
        except Exception as e:
            answer = f"Error: {str(e)}"
        
        confidence = self.crag.evaluate_confidence(user_query, graph_results, vector_results)
        self.state.update(analysis, {'graph': graph_results, 'vector': vector_results})
        
        return {
            'answer': answer,
            'analysis': analysis,
            'allocation': allocation,
            'graph_results': graph_results,
            'vector_results': vector_results,
            'confidence': confidence,
            'from_cache': False
        }
    
    def close(self):
        """Cleanup"""
        self.graph_rag.close()
        self.risk_engine.close()
        self.route_optimizer.close()
        self.neo4j.close()
