from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .models import CampaignRequest, CampaignResponse, HealthResponse, SearchRequest
from .services import marketing_ai_service
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

@app.post("/search")
async def search_insights(request: SearchRequest):
    """Search for competitors or trending keywords"""
    try:
        if request.search_type == "competitors":
            results = marketing_ai_service.search_service.search_competitors(request.query)
        else:
            results = marketing_ai_service.search_service.search_trending_keywords(request.query)
        
        return {
            "query": request.query,
            "type": request.search_type,
            "results": results
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
            "Interactive Conversation Flow", 
            "Competitor & Trend Research",
            "Campaign Strategy Generation",
            "Multi-Platform Content Creation"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )