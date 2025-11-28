from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .models import CampaignRequest, CampaignResponse, HealthResponse, BannerRequest, BannerResponse, MultipleBannersResponse
from .services import marketing_ai_service
from .banner_service import banner_generator

from .config import settings
import uuid
import time

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EnhanceContextRequest(BaseModel):
    user_id: str

@app.post("/chat", response_model=CampaignResponse)
async def chat_endpoint(request: CampaignRequest):
    """Main chat endpoint with enhanced marketing capabilities"""
    try:
        start_time = time.time()
        
        response = marketing_ai_service.generate_response(
            request.user_id, 
            request.message
        )
        
        processing_time = time.time() - start_time
        print(f"Request processed in {processing_time:.2f}s for user {request.user_id}")
        
        return CampaignResponse(**response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/campaign/generate-now")
async def generate_campaign_now(request: CampaignRequest):
    """Force campaign generation with current context"""
    try:
        response = marketing_ai_service._generate_campaign_with_current_context(
            request.user_id
        )
        return CampaignResponse(**response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search/enhance-context")
async def enhance_context_with_search(request: EnhanceContextRequest):
    """Enhance current context with web search"""
    try:
        context = marketing_ai_service.conversation_contexts.get(request.user_id)
        if not context:
            raise HTTPException(status_code=404, detail="User context not found")
        
        # Enhance with web search
        enhanced_context = marketing_ai_service._enhance_context_with_web_search(context)
        
        return {
            "message": "Context enhanced with web search data",
            "enhanced_context": enhanced_context,
            "web_enhanced": enhanced_context.web_enhanced
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/conversation/{user_id}/reset")
async def reset_conversation(user_id: str):
    """Reset conversation for a user"""
    try:
        initial_response = marketing_ai_service.initialize_conversation(user_id)
        return {
            "message": "Conversation reset successfully", 
            "initial_response": initial_response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversation/{user_id}/context")
async def get_conversation_context(user_id: str):
    """Get current conversation context"""
    try:
        context = marketing_ai_service.conversation_contexts.get(user_id)
        state = marketing_ai_service.conversation_states.get(user_id)
        
        if not context:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {
            "context": context,
            "state": state,
            "missing_fields": marketing_ai_service.get_missing_fields(context)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
        model=settings.ollama_model
    )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "features": [
            "User Context Understanding",
            "Interactive Conversation Flow with Early Exit", 
            "Real Web Search via Serper API",
            "Competitor & Trend Research",
            "Campaign Strategy Generation",
            "Multi-Platform Content Creation"
        ],
        "early_generation_commands": [
            "generate campaign now",
            "create campaign now", 
            "use what you have",
            "proceed with current information"
        ]
    }

@app.post("/banners/generate", response_model=BannerResponse)
async def generate_campaign_banner_route(request: BannerRequest):
    """Generate a single campaign banner"""
    try:
        result = banner_generator.generate_campaign_banner(
            context=request.context,
            aspect_ratio=request.aspect_ratio
        )
        return BannerResponse(**result)
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=f"Banner generation failed: {str(e)}")

@app.post("/banners/generate-multiple", response_model=MultipleBannersResponse)
async def generate_multiple_banners(request: BannerRequest):
    """Generate banners for multiple platforms"""
    try:
        results = banner_generator.generate_multiple_platform_banners(request.context)
        return MultipleBannersResponse(
            success=True,
            banners=results,
            message="Multiple banners generated successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multiple banner generation failed: {str(e)}")

@app.post("/campaign/{user_id}/generate-banners")
async def generate_banners_from_context(user_id: str, aspect_ratio: str = "16:9"):
    """Generate banners using existing campaign context"""
    try:
        context = marketing_ai_service.conversation_contexts.get(user_id)
        if not context:
            raise HTTPException(status_code=404, detail="No campaign context found")
        
        # Convert context to dictionary
        context_dict = context.dict()
        
        result = banner_generator.generate_campaign_banner(
            context=context_dict,
            aspect_ratio=aspect_ratio
        )
        
        return BannerResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Banner generation failed: {str(e)}")
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )