#!/usr/bin/env python3
"""
Groq Client: Fast LLM inference with System Prompt
"""
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class GroqClient:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env")
        
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
        
        # System prompt for TITAN
        self.system_prompt = """You are TITAN AI, an expert supply chain intelligence assistant.

        Your role:
        - Analyze supply chain data (factories, warehouses, ports, routes, risks)
        - Provide clear, actionable insights
        - Be concise but informative
        - Use emojis sparingly for emphasis
        - Format responses with markdown headers and lists

        Response format:
        1. Start with a brief summary (1-2 sentences)
        2. Use ## for main sections
        3. Use bullet points for lists
        4. Include numbers and statistics when available

        Keep responses under 300 words."""
        
        print("✅ Groq LLM initialized")
    
    def generate(self, prompt, context=None, max_tokens=1000):
        """Generate response - NO DOUBLE PRINTING"""
        full_prompt = prompt
        
        if context:
            full_prompt = f"""Based on the following data, answer the user's question.

    DATA:
    {self._format_context(context)}

    USER QUESTION: {prompt}

    Provide a clear, structured response."""
        
        try:
            # REMOVE THIS LINE: print("🤖 Calling Groq LLM...")  
            
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.3
            )
            
            response = completion.choices[0].message.content
            # REMOVE THIS LINE: print("✅ LLM response generated")
            return response
            
        except Exception as e:
            return f"Error: {str(e)}"

    
    def _format_context(self, context):
        """Format context dictionary into readable text"""
        formatted = []
        
        for key, value in context.items():
            if isinstance(value, list):
                formatted.append(f"{key.upper()}: {len(value)} items")
                for i, item in enumerate(value[:5], 1):  # First 5 items
                    formatted.append(f"  {i}. {self._format_item(item)}")
            elif isinstance(value, dict):
                formatted.append(f"{key.upper()}:")
                for k, v in value.items():
                    formatted.append(f"  {k}: {v}")
            else:
                formatted.append(f"{key.upper()}: {value}")
        
        return "\n".join(formatted)
    
    def _format_item(self, item):
        """Format individual item"""
        if isinstance(item, dict):
            # Extract key fields
            if 'name' in item:
                return item['name']
            elif 'id' in item:
                return item['id']
            else:
                return str(item)[:50]
        return str(item)[:50]
