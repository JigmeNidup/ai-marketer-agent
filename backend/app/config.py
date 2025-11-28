from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Optional

class Settings(BaseSettings):
    # Application settings
    app_name: str = "Marketing AI Assistant"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Ollama settings
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "deepseek-v3.1:671b-cloud"
    ollama_timeout: int = 300
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: List[str] = ["http://localhost:3000"]
    
    # Conversation settings
    max_conversation_age: int = 36000
    required_fields: List[str] = [
        'target_audience', 'brand_tone', 'campaign_goals', 
        'preferred_platforms', 'product_details'
    ]
    optional_fields: List[str] = [
        'competitors', 'trending_keywords', 'product_references', 
        'key_messages', 'budget', 'timeline'
    ]
    
    # Model settings
    max_tokens: int = 4000
    temperature: float = 0.7
    
    # Web search settings
    enable_web_search: bool = True
    serper_api_key: Optional[str] = None
    serper_api_url: str = "https://google.serper.dev/search"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()