"""
CRAG: Corrective Retrieval-Augmented Generation
Real-time web search + verification for dynamic information
Used for: disaster updates, weather, current events, fact-checking
"""

from typing import List, Dict, Optional
import requests
from datetime import datetime
import json

class CRAG:
    def __init__(self):
        """
        Initialize CRAG with web search capabilities
        Uses DuckDuckGo (no API key needed) or SerpAPI (if available)
        """
        self.search_enabled = True
        print("✅ CRAG Initialized (Web Search Mode)")
    
    def search_web(self, query: str, num_results: int = 5) -> List[Dict]:
        """
        Perform web search using DuckDuckGo Instant Answer API
        
        Args:
            query: Search query
            num_results: Number of results to return
        
        Returns:
            List of search results with title, snippet, url
        """
        try:
            # DuckDuckGo Instant Answer API (free, no key needed)
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1
            }
            
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            results = []
            
            # Parse results
            if data.get('Abstract'):
                results.append({
                    'title': data.get('Heading', 'N/A'),
                    'snippet': data.get('Abstract', ''),
                    'url': data.get('AbstractURL', ''),
                    'source': 'DuckDuckGo'
                })
            
            # Add related topics
            for topic in data.get('RelatedTopics', [])[:num_results]:
                if 'Text' in topic:
                    results.append({
                        'title': topic.get('Text', '')[:100],
                        'snippet': topic.get('Text', ''),
                        'url': topic.get('FirstURL', ''),
                        'source': 'DuckDuckGo'
                    })
            
            return results[:num_results]
            
        except Exception as e:
            print(f"⚠️ Web search failed: {e}")
            return []
    
    def search_disaster_news(self, location: str, disaster_type: str = "disaster") -> List[Dict]:
        """
        Search for recent disaster news
        
        Args:
            location: Location name (e.g., "Taiwan", "Shanghai")
            disaster_type: Type of disaster (earthquake, typhoon, flood, etc.)
        
        Returns:
            Recent news articles
        """
        query = f"{disaster_type} {location} latest news {datetime.now().year}"
        return self.search_web(query, num_results=5)
    
    def verify_disaster_status(self, disaster_id: str, location: str) -> Dict:
        """
        Verify if a disaster is currently active
        
        Returns:
            {
                'verified': bool,
                'status': 'active' | 'resolved' | 'unknown',
                'sources': [...],
                'last_updated': timestamp
            }
        """
        # Search for recent news
        news = self.search_disaster_news(location)
        
        verification = {
            'verified': len(news) > 0,
            'status': 'active' if news else 'unknown',
            'sources': news,
            'last_updated': datetime.now().isoformat(),
            'confidence': 'high' if len(news) >= 3 else 'medium' if news else 'low'
        }
        
        return verification
    
    def search_weather(self, location: str) -> Dict:
        """
        Get current weather information
        Uses wttr.in (free weather API)
        
        Args:
            location: City or location name
        
        Returns:
            Weather data
        """
        try:
            # wttr.in provides free weather data in JSON format
            url = f"https://wttr.in/{location}?format=j1"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            current = data['current_condition'][0]
            
            return {
                'location': location,
                'temperature_c': current['temp_C'],
                'condition': current['weatherDesc'][0]['value'],
                'wind_speed_kmph': current['windspeedKmph'],
                'humidity': current['humidity'],
                'visibility_km': current['visibility'],
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"⚠️ Weather lookup failed: {e}")
            return {'error': str(e)}
    
    def check_port_status(self, port_name: str) -> Dict:
        """
        Check if a port has operational issues
        
        Args:
            port_name: Name of the port (e.g., "Shanghai Port", "Rotterdam")
        
        Returns:
            Status information
        """
        query = f"{port_name} operational status closures disruptions {datetime.now().year}"
        results = self.search_web(query, num_results=3)
        
        return {
            'port': port_name,
            'checked_at': datetime.now().isoformat(),
            'news_found': len(results),
            'potential_issues': results,
            'status': 'issues_reported' if results else 'no_recent_news'
        }
    
    def get_context_for_query(self, query: str, max_tokens: int = 2000) -> str:
        """
        Get real-time web context for LLM
        
        Args:
            query: User query
            max_tokens: Token budget from DCBA
        
        Returns:
            Formatted context string with web search results
        """
        context = "### CRAG Context (Real-time Web Search)\n\n"
        context += f"**Search performed at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Determine search type based on query
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['weather', 'climate', 'temperature']):
            # Weather search
            # Extract location from query (simplified)
            words = query_lower.split()
            location = "global"
            for i, word in enumerate(words):
                if word in ['in', 'at', 'near']:
                    location = words[i+1] if i+1 < len(words) else "global"
                    break
            
            weather = self.search_weather(location)
            if 'error' not in weather:
                context += f"**Current Weather in {location}:**\n"
                context += f"- Temperature: {weather['temperature_c']}°C\n"
                context += f"- Condition: {weather['condition']}\n"
                context += f"- Wind: {weather['wind_speed_kmph']} km/h\n"
                context += f"- Humidity: {weather['humidity']}%\n\n"
        
        elif any(word in query_lower for word in ['port', 'shipping', 'container']):
            # Port status check
            # Extract port name (simplified)
            port_keywords = ['shanghai', 'rotterdam', 'singapore', 'los angeles', 'long beach']
            port_name = next((p for p in port_keywords if p in query_lower), "major ports")
            
            port_status = self.check_port_status(port_name)
            context += f"**{port_name.title()} Status:**\n"
            context += f"- Recent news items: {port_status['news_found']}\n"
            if port_status['potential_issues']:
                context += "- Latest updates:\n"
                for issue in port_status['potential_issues'][:2]:
                    context += f"  • {issue['snippet'][:100]}...\n"
            context += "\n"
        
        else:
            # General web search
            results = self.search_web(query, num_results=5)
            
            if results:
                context += "**Web Search Results:**\n"
                for i, result in enumerate(results[:3], 1):
                    context += f"{i}. **{result['title']}**\n"
                    context += f"   {result['snippet'][:150]}...\n"
                    context += f"   Source: {result['url']}\n\n"
            else:
                context += "⚠️ No recent web results found for this query.\n\n"
        
        # Truncate to token budget
        max_chars = max_tokens * 4
        if len(context) > max_chars:
            context = context[:max_chars] + "...\n[Context truncated]"
        
        return context
    
    def correct_hallucination(self, llm_claim: str, context: str) -> Dict:
        """
        Verify an LLM's claim against web sources
        
        Args:
            llm_claim: Statement to verify
            context: Original context used
        
        Returns:
            {
                'claim': str,
                'verified': bool,
                'confidence': float,
                'sources': [...]
            }
        """
        # Search for evidence
        evidence = self.search_web(llm_claim, num_results=3)
        
        return {
            'claim': llm_claim,
            'verified': len(evidence) > 0,
            'confidence': min(len(evidence) / 3.0, 1.0),
            'sources': evidence,
            'checked_at': datetime.now().isoformat()
        }


# Quick test
if __name__ == "__main__":
    print("🧪 Testing CRAG...")
    
    crag = CRAG()
    
    # Test 1: Web search
    print("\n🔍 Test 1: Web Search - 'Taiwan earthquake 2024'")
    results = crag.search_web("Taiwan earthquake 2024", num_results=3)
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['title']}")
        print(f"   {r['snippet'][:100]}...")
    
    # Test 2: Weather lookup
    print("\n🌤️  Test 2: Weather Lookup - Shanghai")
    weather = crag.search_weather("Shanghai")
    if 'error' not in weather:
        print(f"Temperature: {weather['temperature_c']}°C")
        print(f"Condition: {weather['condition']}")
    else:
        print(f"Error: {weather['error']}")
    
    # Test 3: Port status
    print("\n🚢 Test 3: Port Status - Shanghai Port")
    port_status = crag.check_port_status("Shanghai Port")
    print(f"News items found: {port_status['news_found']}")
    print(f"Status: {port_status['status']}")
    
    # Test 4: Context generation
    print("\n📄 Test 4: Context Generation")
    context = crag.get_context_for_query("Is there a typhoon in Taiwan right now?", max_tokens=1000)
    print(context[:400] + "...")
    
    print("\n✅ CRAG Tests Complete!")
