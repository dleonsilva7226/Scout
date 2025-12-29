"""Configuration for Scout"""
import os
from dotenv import load_dotenv

load_dotenv()

# Ollama Configuration (primary, free option)
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
# Available Ollama Cloud models: deepseek-v3.2, qwen3-next:80b, glm-4.7, mistral-large-3:675b, etc.
# Default: deepseek-v3.2 (good for structured extraction tasks)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-v3.2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://ollama.com")

# OpenAI Configuration (fallback option)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Google Sheets Configuration
GOOGLE_SHEETS_CREDS = os.getenv("GOOGLE_SHEETS_CREDS")
GOOGLE_SPREADSHEET_ID = os.getenv("GOOGLE_SPREADSHEET_ID")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")  # gid from URL (optional, uses first sheet if not set)

# RAG Configuration
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

def validate_config():
    """Validate that at least one LLM API key is present"""
    if not OLLAMA_API_KEY and not OPENAI_API_KEY:
        raise ValueError(
            "At least one LLM API key is required.\n"
            "Set OLLAMA_API_KEY (free) or OPENAI_API_KEY (fallback) in your .env file:\n"
            "  OLLAMA_API_KEY=your-ollama-key\n"
            "  OPENAI_API_KEY=your-openai-key  # Optional fallback"
        )
    return True
