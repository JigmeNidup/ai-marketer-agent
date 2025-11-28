from pydantic import BaseModel, Field, field_validator
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
    target_audience: Optional[str] = None
    brand_tone: Optional[BrandTone] = None
    campaign_goals: List[CampaignGoal] = []
    preferred_platforms: List[Platform] = []
    product_details: Optional[str] = None
    
    # Enhanced optional fields
    competitors: List[str] = []
    trending_keywords: List[str] = []
    product_references: List[str] = []
    key_messages: List[str] = []
    budget: Optional[str] = None
    timeline: Optional[str] = None
    unique_selling_points: List[str] = []
    web_enhanced: bool = False
    
    @field_validator('campaign_goals', mode='before')
    @classmethod
    def validate_campaign_goals(cls, v):
        if isinstance(v, list):
            validated_goals = []
            for goal in v:
                # Handle both enum values and string values
                if isinstance(goal, CampaignGoal):
                    validated_goals.append(goal)
                elif isinstance(goal, str):
                    # Map 'awareness' to 'brand_awareness'
                    if goal == 'awareness':
                        validated_goals.append(CampaignGoal.AWARENESS)
                    elif goal == 'brand_awareness':
                        validated_goals.append(CampaignGoal.AWARENESS)
                    elif goal == 'conversion' or goal == 'conversions':
                        validated_goals.append(CampaignGoal.CONVERSION)
                    elif goal == 'engagement':
                        validated_goals.append(CampaignGoal.ENGAGEMENT)
                    elif goal == 'lead_generation' or goal == 'lead generation':
                        validated_goals.append(CampaignGoal.LEAD_GENERATION)
                    else:
                        # Try to match the goal directly
                        try:
                            validated_goals.append(CampaignGoal(goal))
                        except ValueError:
                            # Skip invalid goals
                            continue
            return validated_goals
        return v
    
    # Context management methods
    def merge_context(self, updates: Dict[str, Any]) -> 'UserContext':
        """Merge updates into current context without overwriting existing data"""
        context_dict = self.model_dump()
        
        for field, value in updates.items():
            if hasattr(self, field) and value is not None:
                current_value = getattr(self, field)
                
                if isinstance(current_value, list) and isinstance(value, list):
                    # Merge lists, avoid duplicates
                    merged_list = current_value + [item for item in value if item not in current_value]
                    context_dict[field] = merged_list
                elif isinstance(current_value, list) and not isinstance(value, list):
                    # Convert single value to list
                    if value not in current_value:
                        context_dict[field] = current_value + [value]
                elif isinstance(current_value, str) and isinstance(value, str):
                    # For strings, only update if current is empty or new value is more specific
                    if not current_value or len(value) > len(current_value):
                        context_dict[field] = value
                else:
                    # For other types, update if current is None/empty
                    if not current_value:
                        context_dict[field] = value
        
        return UserContext(**context_dict)
    
    def is_complete(self) -> bool:
        """Check if all required fields are filled"""
        required_fields = ['target_audience', 'brand_tone', 'campaign_goals', 'preferred_platforms', 'product_details']
        for field in required_fields:
            value = getattr(self, field)
            if value is None or (isinstance(value, list) and len(value) == 0):
                return False
        return True
    
    def get_missing_fields(self) -> List[str]:
        """Get list of missing required fields"""
        missing = []
        required_fields = ['target_audience', 'brand_tone', 'campaign_goals', 'preferred_platforms', 'product_details']
        for field in required_fields:
            value = getattr(self, field)
            if value is None or (isinstance(value, list) and len(value) == 0):
                missing.append(field)
        return missing
    
    def to_prompt_context(self) -> str:
        """Convert context to string for AI prompts"""
        context_parts = []
        
        if self.product_details:
            context_parts.append(f"Product: {self.product_details}")
        if self.target_audience:
            context_parts.append(f"Target Audience: {self.target_audience}")
        if self.brand_tone:
            # Safe access to enum value
            tone_value = self.brand_tone.value if hasattr(self.brand_tone, 'value') else str(self.brand_tone)
            context_parts.append(f"Brand Tone: {tone_value}")
        if self.campaign_goals:
            # Safe conversion of enum goals to strings
            goals_str = ', '.join([
                goal.value if hasattr(goal, 'value') else str(goal)
                for goal in self.campaign_goals
            ])
            context_parts.append(f"Campaign Goals: {goals_str}")
        if self.preferred_platforms:
            # Safe conversion of enum platforms to strings
            platforms_str = ', '.join([
                platform.value if hasattr(platform, 'value') else str(platform)
                for platform in self.preferred_platforms
            ])
            context_parts.append(f"Platforms: {platforms_str}")
        if self.budget:
            context_parts.append(f"Budget: {self.budget}")
        if self.timeline:
            context_parts.append(f"Timeline: {self.timeline}")
        if self.competitors:
            context_parts.append(f"Competitors: {', '.join(self.competitors)}")
        if self.trending_keywords:
            context_parts.append(f"Trending Topics: {', '.join(self.trending_keywords)}")
        if self.key_messages:
            # Handle both string and list formats safely
            if isinstance(self.key_messages, list):
                context_parts.append(f"Key Messages: {', '.join([str(msg) for msg in self.key_messages])}")
            else:
                context_parts.append(f"Key Messages: {self.key_messages}")
        if self.unique_selling_points:
            context_parts.append(f"Unique Selling Points: {', '.join(self.unique_selling_points)}")
        
        return "\n".join(context_parts) if context_parts else "No context collected yet"
    class Config:
        use_enum_values = True
        extra = "ignore"  # Ignore extra fields instead of throwing errors

class ConversationState(str, Enum):
    COLLECTING_CONTEXT = "collecting_context"
    GATHERING_INSIGHTS = "gathering_insights"
    READY_FOR_CAMPAIGN = "ready_for_campaign"
    GENERATING_CAMPAIGN = "generating_campaign"

class ChatMessage(BaseModel):
    message: str = ""
    is_user: bool = False
    timestamp: str = ""

class CampaignRequest(BaseModel):
    user_id: str = ""
    message: str = ""

class CampaignResponse(BaseModel):
    response: str = ""
    context: UserContext = Field(default_factory=UserContext)
    state: ConversationState = ConversationState.COLLECTING_CONTEXT
    is_complete: bool = False
    campaign_content: Optional[Dict[str, Any]] = None
    
    class Config:
        use_enum_values = True

class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = settings.app_name
    version: str = settings.app_version
    model: str = settings.ollama_model

class SearchRequest(BaseModel):
    query: str = ""
    search_type: str = "competitors"

class BannerRequest(BaseModel):
    user_id: str = ""
    context: Dict[str, Any] = Field(default_factory=dict)
    aspect_ratio: str = "16:9"
    generate_for_all_platforms: bool = False

class BannerResponse(BaseModel):
    success: bool = False
    image_data: Optional[str] = None
    prompt: Optional[str] = None
    aspect_ratio: Optional[str] = None
    dimensions: Optional[str] = None
    platform: Optional[str] = None
    description: Optional[str] = None
    error: Optional[str] = None
    message: str = ""

class MultipleBannersResponse(BaseModel):
    success: bool = False
    banners: Dict[str, BannerResponse] = Field(default_factory=dict)
    message: str = ""

# Helper function to safely convert context for banner generation
def context_to_dict(context: UserContext) -> Dict[str, Any]:
    """Safely convert UserContext to dictionary for banner generation"""
    try:
        data = context.model_dump()
        
        # Convert enum values to strings safely
        if data.get('brand_tone') and hasattr(data['brand_tone'], 'value'):
            data['brand_tone'] = data['brand_tone'].value
        
        if data.get('campaign_goals'):
            data['campaign_goals'] = [
                goal.value if hasattr(goal, 'value') else str(goal)
                for goal in data['campaign_goals']
            ]
            
        if data.get('preferred_platforms'):
            data['preferred_platforms'] = [
                platform.value if hasattr(platform, 'value') else str(platform)
                for platform in data['preferred_platforms']
            ]
            
        return data
    except Exception as e:
        print(f"Error converting context to dict: {e}")
        # Fallback to basic conversion
        return {
            'product_details': context.product_details or '',
            'target_audience': context.target_audience or '',
            'brand_tone': context.brand_tone.value if context.brand_tone and hasattr(context.brand_tone, 'value') else str(context.brand_tone) if context.brand_tone else 'professional',
            'campaign_goals': [
                goal.value if hasattr(goal, 'value') else str(goal)
                for goal in (context.campaign_goals or [])
            ],
            'key_messages': context.key_messages if isinstance(context.key_messages, list) else [context.key_messages] if context.key_messages else []
        }