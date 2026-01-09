from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.utils.config import Config


class GeminiClient:
    def __init__(self, model="gemini-2.5-flash", temperature=0):
        """
        Initialize Gemini client with LangChain wrapper.
        
        Args:
            model: Gemini model name (default: gemini-2.5-flash)
            temperature: Sampling temperature (0-1)
        """
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in config")
        
        # LangChain wrapper for easy integration
        self.llm = ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=Config.GEMINI_API_KEY,
        )
        
        self.model_name = model
        
    def get_llm(self):
        """Returns LangChain-compatible LLM"""
        return self.llm
        
    def generate_response(self, prompt: str, max_tokens: int = 2000):
        """
        Generate a simple text response.
        
        Args:
            prompt: User prompt
            max_tokens: Maximum tokens (not used by Gemini API directly)
            
        Returns:
            Generated text response
        """
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            print(f"❌ Gemini API Error: {e}")
            return f"Error: {str(e)}"
    
    def generate_with_context(self, system_prompt: str, user_query: str):
        """
        Generate with system instructions using proper message format.
        
        Args:
            system_prompt: System instructions
            user_query: User query
            
        Returns:
            Generated text response
        """
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_query)
            ]
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            print(f"❌ Gemini API Error: {e}")
            return f"Error: {str(e)}"


# Quick test
if __name__ == "__main__":
    client = GeminiClient()
    
    # Test 1: Simple response
    response = client.generate_response("What is supply chain analytics?")
    print(f"✅ Test 1 Response: {response[:200]}...")
    
    # Test 2: With system context
    system = "You are a helpful AI assistant specializing in business analytics."
    query = "Explain product analytics in one sentence."
    response2 = client.generate_with_context(system, query)
    print(f"\n✅ Test 2 Response: {response2}")
