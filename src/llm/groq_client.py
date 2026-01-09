#!/usr/bin/env python3
"""
Groq LLM Client - Fast inference with LLaMA models
"""

from groq import Groq
from src.utils.config import Config
from typing import Optional
import asyncio


class GroqLLM:
    """
    Wrapper for Groq API (fast open-source model inference)
    """
    
    def __init__(self, model: str = "llama-3.3-70b-versatile", temperature: float = 0.7):
        """
        Initialize Groq client
        
        Args:
            model: Model name (default: llama-3.3-70b-versatile)
            temperature: Sampling temperature (0.0-1.0)
        """
        self.client = Groq(api_key=Config.GROQ_API_KEY)
        self.model = model
        self.temperature = temperature
        
        # Groq's fast models
        self.available_models = [
            "llama-3.3-70b-versatile",      # Best balance
            "llama-3.1-70b-versatile",      # Fast
            "mixtral-8x7b-32768",            # Long context
            "gemma2-9b-it"                   # Lightweight
        ]
    
    def generate(self, prompt: str, temperature: Optional[float] = None, max_tokens: int = 2048) -> str:
        """
        Generate text completion
        
        Args:
            prompt: Input prompt
            temperature: Override default temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        temp = temperature if temperature is not None else self.temperature
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful supply chain AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temp,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"❌ Groq API Error: {e}")
            return f"Error: {str(e)}"
    
    async def generate_async(self, prompt: str, temperature: float = None) -> str:
        """
        Async wrapper for generate() method
        (Groq SDK is sync, so we run in executor)
        """
        loop = asyncio.get_event_loop()
        temp = temperature if temperature is not None else self.temperature
        return await loop.run_in_executor(None, self.generate, prompt, temp)
    
    def get_llm(self):
        """
        Return self for compatibility with LangChain-style usage
        """
        return self


# ============================================================================
# TESTS
# ============================================================================

if __name__ == "__main__":
    print("🧪 Testing Groq Client...")
    
    llm = GroqLLM(temperature=0.2)
    
    # Test 1: Simple generation
    print("\n📝 Test 1: Simple Query")
    response = llm.generate("What is supply chain management? Answer in 2 sentences.")
    print(f"Response: {response}")
    
    # Test 2: Async generation
    print("\n📝 Test 2: Async Query")
    async def test_async():
        response = await llm.generate_async("List 3 types of supply chain disruptions.")
        print(f"Response: {response}")
    
    asyncio.run(test_async())
    
    print("\n✅ Groq Tests Complete!")
