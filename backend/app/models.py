from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from .config import settings

class CampaignGoal(str, Enum):
    AWARENESS = "brand_awareness"
    CONVERSION = "conversions"
    ENGAGEMENT = "engagement"
    LEAD_GENERATION = "lead_generation"

class BrandTone(str, Enum):
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    FUNNY = "funny"
    INSPIRATIONAL = "inspirational"
    AUTHORITATIVE = "authoritative"

class Platform(str, Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    EMAIL = "email"
    GOOGLE_ADS = "google_ads"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"

class UserContext(BaseModel):
    # Required fields
    target_audience: Optional[str] = Field(
        default=None,
        description="Detailed description of target audience demographics, interests, and behaviors"
    )
    brand_tone: Optional[BrandTone] = Field(
        default=None,
        description="Voice and personality of the brand"
    )
    campaign_goals: Optional[List[CampaignGoal]] = Field(
        default_factory=list,
        description="Primary objectives for the campaign"
    )
    preferred_platforms: Optional[List[Platform]] = Field(
        default_factory=list,
        description="Marketing channels to utilize"
    )
    product_details: Optional[str] = Field(
        default=None,
        description="Comprehensive product/service information, features, and benefits"
    )
    
    # Enhanced optional fields
    competitors: Optional[List[str]] = Field(
        default_factory=list,
        description="Key competitors and their market positioning"
    )
    trending_keywords: Optional[List[str]] = Field(
        default_factory=list,
        description="Relevant trending topics and search terms"
    )
    product_references: Optional[List[str]] = Field(
        default_factory=list,
        description="Similar products or inspirational references"
    )
    key_messages: Optional[List[str]] = Field(
        default_factory=list,
        description="Core brand messages and value propositions"
    )
    budget: Optional[str] = Field(
        default=None,
        description="Campaign budget constraints and allocation"
    )
    timeline: Optional[str] = Field(
        default=None,
        description="Campaign schedule and key milestones"
    )
    unique_selling_points: Optional[List[str]] = Field(
        default_factory=list,
        description="What makes the product/service unique"
    )
    web_enhanced: bool = Field(
        default=False,
        description="Whether context has been enhanced with web search"
    )
    
    class Config:
        use_enum_values = True

class ConversationState(str, Enum):
    COLLECTING_CONTEXT = "collecting_context"
    GATHERING_INSIGHTS = "gathering_insights"
    READY_FOR_CAMPAIGN = "ready_for_campaign"
    GENERATING_CAMPAIGN = "generating_campaign"

class ChatMessage(BaseModel):
    message: str = Field(..., description="The message content")
    is_user: bool = Field(..., description="Whether the message is from user or AI")
    timestamp: str = Field(..., description="ISO timestamp of the message")

class CampaignRequest(BaseModel):
    user_id: str = Field(..., description="Unique identifier for the user")
    message: str = Field(..., description="User's message content")

class CampaignResponse(BaseModel):
    response: str = Field(..., description="AI response message")
    context: UserContext = Field(..., description="Current conversation context")
    state: ConversationState = Field(..., description="Current conversation state")
    is_complete: bool = Field(..., description="Whether campaign generation is complete")
    campaign_content: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Generated campaign content when complete"
    )
    
    class Config:
        use_enum_values = True

class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(default=settings.app_version, description="API version")
    model: str = Field(default=settings.ollama_model, description="Active AI model")

class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query for competitors or trends")
    search_type: str = Field(default="competitors", description="Type of search: competitors or trends")