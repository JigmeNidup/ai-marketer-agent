from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Optional, Dict, Any
from pydantic import validator

class Settings(BaseSettings):
    # Application settings
    app_name: str = "Marketing AI Assistant"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"  # development, staging, production
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    cors_origins: List[str] = [
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:8000"
    ]
    
    # Ollama settings
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "deepseek-v3.1:671b-cloud"  # Fallback model
    preferred_models: List[str] = [
        "deepseek-v3.1:671b-cloud",
        "llama2", 
        "mistral",
        "codellama"
    ]
    ollama_timeout: int = 300
    ollama_keep_alive: str = "5m"
    
    # Model generation settings
    max_tokens: int = 4000
    temperature: float = 0.7
    top_k: int = 40
    top_p: float = 0.9
    repeat_penalty: float = 1.1
    
    # Conversation settings
    max_conversation_age: int = 36000  # 10 hours in seconds
    max_conversation_history: int = 20  # Number of messages to keep
    conversation_cleanup_interval: int = 3600  # 1 hour in seconds
    
    # Required fields for campaign generation
    required_fields: List[str] = [
        'target_audience', 
        'brand_tone', 
        'campaign_goals', 
        'preferred_platforms', 
        'product_details'
    ]
    
    # Optional fields for enhanced campaigns
    optional_fields: List[str] = [
        'competitors', 
        'trending_keywords', 
        'product_references', 
        'key_messages', 
        'budget', 
        'timeline',
        'unique_selling_points'
    ]
    
    # Web search settings
    enable_web_search: bool = True
    serper_api_key: Optional[str] = None
    serper_api_url: str = "https://google.serper.dev/search"
    max_search_results: int = 5
    search_timeout: int = 10
    
    # Banner generation settings
    enable_banner_generation: bool = True
    fal_api_key: Optional[str] = None
    default_banner_aspect_ratio: str = "16:9"
    banner_generation_timeout: int = 30
    supported_aspect_ratios: List[str] = [
        "1:1", "16:9", "9:16", "4:3", "3:4", "2:3"
    ]
    
    # Campaign generation settings
    max_campaign_retries: int = 3
    campaign_generation_timeout: int = 120
    enable_campaign_templates: bool = True
    
    # Security settings
    rate_limit_requests: int = 100  # requests per minute
    rate_limit_window: int = 60  # seconds
    enable_rate_limiting: bool = True
    
    # Logging settings
    log_level: str = "INFO"
    enable_request_logging: bool = True
    enable_response_logging: bool = False  # Be careful with sensitive data
    
    # Storage settings (for future persistence)
    enable_persistence: bool = False
    database_url: Optional[str] = None
    redis_url: Optional[str] = None
    
    # Monitoring settings
    enable_health_checks: bool = True
    health_check_interval: int = 30  # seconds
    enable_metrics: bool = True
    
    # Feature flags
    enable_ai_context_extraction: bool = True
    enable_conversation_analytics: bool = True
    enable_campaign_export: bool = True
    enable_real_time_updates: bool = False

    # Validation methods
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @validator("preferred_models", pre=True)
    def parse_preferred_models(cls, v):
        if isinstance(v, str):
            return [model.strip() for model in v.split(",")]
        return v

    @validator("environment")
    def validate_environment(cls, v):
        allowed_environments = ["development", "staging", "production"]
        if v not in allowed_environments:
            raise ValueError(f"Environment must be one of {allowed_environments}")
        return v

    @validator("log_level")
    def validate_log_level(cls, v):
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"Log level must be one of {allowed_levels}")
        return v.upper()

    def get_ollama_model(self) -> str:
        """Get the best available Ollama model"""
        # In a real implementation, you would check which models are available
        # and return the first one from preferred_models that exists
        return self.ollama_model

    def is_development(self) -> bool:
        return self.environment == "development"

    def is_production(self) -> bool:
        return self.environment == "production"

    def get_cors_origins(self) -> List[str]:
        """Get CORS origins with environment-specific additions"""
        origins = self.cors_origins.copy()
        
        if self.is_development():
            origins.extend([
                "http://localhost:3001",
                "http://127.0.0.1:3001",
                "http://localhost:8080"
            ])
        
        return origins

    def get_feature_flags(self) -> Dict[str, bool]:
        """Get all feature flags as a dictionary"""
        return {
            "web_search": self.enable_web_search,
            "banner_generation": self.enable_banner_generation,
            "campaign_templates": self.enable_campaign_templates,
            "rate_limiting": self.enable_rate_limiting,
            "persistence": self.enable_persistence,
            "health_checks": self.enable_health_checks,
            "metrics": self.enable_metrics,
            "ai_context_extraction": self.enable_ai_context_extraction,
            "conversation_analytics": self.enable_conversation_analytics,
            "campaign_export": self.enable_campaign_export,
            "real_time_updates": self.enable_real_time_updates,
        }

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        env_prefix = "MARKETING_AI_"  # All env vars should start with MARKETING_AI_

        # Example environment variables:
        # MARKETING_AI_APP_NAME="My Marketing AI"
        # MARKETING_AI_DEBUG=true
        # MARKETING_AI_OLLAMA_MODEL="llama2"
        # MARKETING_AI_SERPER_API_KEY="your_serper_key"
        # MARKETING_AI_FAL_API_KEY="your_fal_key"
        # MARKETING_AI_ENVIRONMENT="production"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

# Global settings instance
settings = get_settings()