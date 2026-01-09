import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root
ROOT_DIR = Path(__file__).parent.parent.parent
load_dotenv(ROOT_DIR / ".env")

class Config:
    # LLM APIs
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # FIX: Was GOOGLE_API_KEY
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")      # Added Groq support
    
    # Neo4j
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "June#12345")
    
    # Vector DB
    CHROMA_DB_PATH = ROOT_DIR / "chroma_db"
    
    # DCBA Settings (The Budget)
    MAX_CONTEXT_TOKENS = 8000
    GRAPH_MAX_HOPS = 6  # Maximum path depth for cascade analysis
    
    # Performance
    BATCH_SIZE = 100
    CACHE_TTL_SECONDS = 300  # 5 minutes
    
    @classmethod
    def validate(cls):
        errors = []
        if not cls.GEMINI_API_KEY and not cls.GROQ_API_KEY:
            errors.append("❌ Neither GEMINI_API_KEY nor GROQ_API_KEY found in .env")
        if not cls.NEO4J_PASSWORD:
            errors.append("❌ NEO4J_PASSWORD is missing in .env")
        
        if errors:
            for err in errors:
                print(err)
            raise ValueError("Configuration validation failed")
        
        print("✅ Config Validated")
        return True

# Validate on import
Config.validate()
