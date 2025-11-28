import ollama
from typing import Dict, Any, List, Tuple
import json
import time
import re
import requests
from .models import UserContext, ConversationState, BrandTone, CampaignGoal, Platform
from .config import settings

class WebSearchService:
    """Mock web search service - can be replaced with actual API"""
    
    def search_competitors(self, product_type: str) -> List[str]:
        """Mock competitor search based on product type"""
        competitor_map = {
            "health": ["Fitbit", "MyFitnessPal", "Headspace", "Calm"],
            "tech": ["Apple", "Samsung", "Google", "Microsoft"],
            "fashion": ["Zara", "H&M", "Nike", "Adidas"],
            "food": ["McDonald's", "Starbucks", "Domino's", "Chipotle"],
            "finance": ["PayPal", "Square", "Robinhood", "Coinbase"],
            "education": ["Coursera", "Udemy", "Khan Academy", "Duolingo"]
        }
        
        for category, competitors in competitor_map.items():
            if category in product_type.lower():
                return competitors
        return ["Industry Leader A", "Emerging Competitor B", "Direct Competitor C"]
    
    def search_trending_keywords(self, industry: str) -> List[str]:
        """Mock trending keywords search"""
        trend_map = {
            "health": ["mindfulness", "wellness", "fitness tracking", "mental health"],
            "tech": ["AI assistants", "smart home", "cybersecurity", "cloud computing"],
            "fashion": ["sustainable fashion", "athleisure", "vintage", "custom fit"],
            "food": ["plant-based", "meal prep", "local sourcing", "food delivery"],
            "finance": ["crypto", "fintech", "digital banking", "investment apps"],
            "education": ["online learning", "skill development", "micro-courses", "career transition"]
        }
        
        for category, trends in trend_map.items():
            if category in industry.lower():
                return trends
        return ["digital transformation", "customer experience", "sustainability", "innovation"]

class MarketingAIService:
    def __init__(self):
        self.conversation_contexts: Dict[str, UserContext] = {}
        self.conversation_states: Dict[str, ConversationState] = {}
        self.conversation_histories: Dict[str, List[Dict]] = {}
        self.last_activity: Dict[str, float] = {}
        self.search_service = WebSearchService()
        
        # Initialize Ollama client
        self.ollama_client = ollama.Client(
            host=settings.ollama_host,
            timeout=settings.ollama_timeout
        )
        
        self._verify_model()
        
        # System prompt for AI behavior
        self.system_prompt = """You are a marketing strategist and creative co-pilot. Your role is to help users create comprehensive, data-driven marketing campaigns.

Key Responsibilities:
1. Understand user requirements through guided questioning
2. Extract and organize marketing context (audience, tone, goals, platforms)
3. Provide strategic marketing insights
4. Generate complete campaign deliverables (ad copy, emails, social posts)
5. Tailor all content to the specific brand context

Always maintain a professional yet approachable tone. Ask one question at a time to avoid overwhelming the user. Provide clear, actionable marketing advice."""

    def _verify_model(self):
        """Verify that the configured model is available"""
        try:
            models = self.ollama_client.list()
            available_models = [model['name'] for model in models['models']]
            
            if settings.ollama_model not in available_models:
                print(f"Warning: Model {settings.ollama_model} not found. Available models: {available_models}")
        except Exception as e:
            print(f"Error verifying model: {e}")

    def initialize_conversation(self, user_id: str) -> str:
        """Initialize a new conversation with system prompt"""
        self.conversation_contexts[user_id] = UserContext()
        self.conversation_states[user_id] = ConversationState.COLLECTING_CONTEXT
        self.conversation_histories[user_id] = []
        self.last_activity[user_id] = time.time()
        
        initial_prompt = f"""{self.system_prompt}

Welcome! I'm your AI Marketing Strategist. I'll help you create a comprehensive marketing campaign step by step.

Let's start by understanding your basics. Tell me about your product or service, and I'll guide you through the rest."""
        
        return initial_prompt

    def get_missing_fields(self, context: UserContext) -> List[str]:
        """Get list of missing required fields"""
        missing = []
        for field in settings.required_fields:
            current_value = getattr(context, field)
            if current_value is None or (isinstance(current_value, list) and len(current_value) == 0):
                missing.append(field)
        return missing

    def get_next_question(self, context: UserContext, state: ConversationState) -> Tuple[str, bool]:
        """Determine the next question based on current context and state"""
        missing_fields = self.get_missing_fields(context)
        
        if state == ConversationState.COLLECTING_CONTEXT and missing_fields:
            field_questions = {
                'target_audience': "🎯 **Target Audience**: Who are you trying to reach? (e.g., 'Young professionals aged 25-35 interested in fitness')",
                'brand_tone': "🎭 **Brand Tone**: How would you describe your brand's personality? (professional, casual, funny, inspirational, authoritative)",
                'campaign_goals': "🎯 **Campaign Goals**: What do you want to achieve? (brand awareness, conversions, engagement, lead generation)",
                'preferred_platforms': "📱 **Platforms**: Where will you market? (Facebook, Instagram, Twitter, LinkedIn, Email, Google Ads, TikTok, YouTube)",
                'product_details': "📦 **Product/Service**: Tell me about what you're offering and its key benefits"
            }
            return field_questions[missing_fields[0]], False
        
        elif state == ConversationState.COLLECTING_CONTEXT and not missing_fields:
            # Move to insights gathering
            return "Great! I have the basics. Now let's gather some strategic insights.\n\nDo you have any specific competitors I should know about, or would you like me to research some based on your industry?", True
        
        elif state == ConversationState.GATHERING_INSIGHTS:
            if not context.competitors:
                return "🔍 **Competitor Research**: Who are your main competitors? (I can also suggest some based on your industry)", False
            elif not context.trending_keywords:
                return "📈 **Market Trends**: Any specific keywords or trends you want to target? (I can research current trends in your space)", False
            elif not context.key_messages:
                return "💡 **Key Messages**: What are your main value propositions or unique selling points?", False
            else:
                return "Ready to create your campaign!", True
        
        return "Is there anything else you'd like to add before we create your campaign?", True

    def update_context_from_message(self, user_id: str, message: str) -> UserContext:
        """Enhanced context extraction with web search integration"""
        context = self.conversation_contexts[user_id]
        state = self.conversation_states[user_id]
        
        # Extract basic context
        updates = self._extract_context_manual(message, context)
        
        # Handle web search requests
        if state == ConversationState.GATHERING_INSIGHTS:
            search_updates = self._handle_insight_requests(message, context)
            updates.update(search_updates)
        
        # Apply updates
        for field, value in updates.items():
            if hasattr(context, field) and value is not None:
                current_value = getattr(context, field)
                if isinstance(current_value, list) and isinstance(value, list):
                    # Merge lists
                    updated_list = current_value + [item for item in value if item not in current_value]
                    setattr(context, field, updated_list)
                else:
                    setattr(context, field, value)
        
        return context

    def _handle_insight_requests(self, message: str, context: UserContext) -> Dict[str, Any]:
        """Handle requests for competitor and trend research"""
        updates = {}
        message_lower = message.lower()
        
        # Check if user wants automated research
        research_triggers = ['research', 'suggest', 'find some', 'look up', 'automate']
        if any(trigger in message_lower for trigger in research_triggers):
            if 'competitor' in message_lower or 'competition' in message_lower:
                if context.product_details:
                    competitors = self.search_service.search_competitors(context.product_details)
                    updates['competitors'] = competitors
            
            if 'trend' in message_lower or 'keyword' in message_lower:
                if context.product_details:
                    trends = self.search_service.search_trending_keywords(context.product_details)
                    updates['trending_keywords'] = trends
        
        return updates

    def _extract_context_manual(self, message: str, current_context: UserContext) -> Dict[str, Any]:
        """Manual context extraction with enhanced field detection"""
        updates = {}
        message_lower = message.lower()
        
        # Enhanced extraction patterns for all field types
        patterns = {
            'target_audience': [
                r'(?:audience|target|customers?|users?).{0,20}?(?:is|are|:)\s*([^.!?]+)',
                r'(?:reach|targeting|focusing on)\s+([^.!?]+?)(?:audience|market|demographic)',
            ],
            'product_details': [
                r'(?:product|service|business|offering).{0,30}?(?:is|are|:)\s*([^.!?]+)',
                r'(?:sell|offer|provide).{0,30}?([^.!?]+)',
            ],
            'competitors': [
                r'(?:competitors?|competition).{0,30}?(?:is|are|:)\s*([^.!?]+)',
                r'(?:competing against|similar to|like).{0,30}?([^.!?]+)',
            ],
            'key_messages': [
                r'(?:message|value|benefit|proposition).{0,30}?(?:is|are|:)\s*([^.!?]+)',
                r'(?:highlight|emphasize|focus on).{0,30}?([^.!?]+)',
            ]
        }
        
        for field, field_patterns in patterns.items():
            for pattern in field_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    value = match.group(1).strip()
                    if value and len(value) > 2:
                        if field in ['competitors', 'key_messages']:
                            # Split lists by common separators
                            items = re.split(r'[,;]|\band\b', value)
                            updates[field] = [item.strip() for item in items if item.strip()]
                        else:
                            updates[field] = value.capitalize()
                        break
        
        # Enum field extraction
        updates.update(self._extract_enum_fields(message))
        
        return updates

    def _extract_enum_fields(self, message: str) -> Dict[str, Any]:
        """Extract enum fields with comprehensive mapping"""
        updates = {}
        message_lower = message.lower()
        
        # Brand tone mapping
        tone_mapping = {
            'professional': BrandTone.PROFESSIONAL,
            'casual': BrandTone.CASUAL,
            'funny': BrandTone.FUNNY,
            'inspirational': BrandTone.INSPIRATIONAL,
            'authoritative': BrandTone.AUTHORITATIVE,
        }
        
        for tone_keyword, tone_enum in tone_mapping.items():
            if tone_keyword in message_lower:
                updates['brand_tone'] = tone_enum
                break
        
        # Campaign goals mapping
        goal_keywords = {
            'brand awareness': CampaignGoal.AWARENESS,
            'awareness': CampaignGoal.AWARENESS,
            'conversions': CampaignGoal.CONVERSION,
            'conversion': CampaignGoal.CONVERSION,
            'engagement': CampaignGoal.ENGAGEMENT,
            'lead generation': CampaignGoal.LEAD_GENERATION,
            'leads': CampaignGoal.LEAD_GENERATION,
        }
        
        detected_goals = []
        for goal_keyword, goal_enum in goal_keywords.items():
            if goal_keyword in message_lower:
                detected_goals.append(goal_enum)
        
        if detected_goals:
            updates['campaign_goals'] = detected_goals
        
        # Platform mapping
        platform_keywords = {
            'facebook': Platform.FACEBOOK,
            'instagram': Platform.INSTAGRAM,
            'twitter': Platform.TWITTER,
            'linkedin': Platform.LINKEDIN,
            'email': Platform.EMAIL,
            'google ads': Platform.GOOGLE_ADS,
            'tiktok': Platform.TIKTOK,
            'youtube': Platform.YOUTUBE,
        }
        
        detected_platforms = []
        for platform_keyword, platform_enum in platform_keywords.items():
            if platform_keyword in message_lower:
                detected_platforms.append(platform_enum)
        
        if detected_platforms:
            updates['preferred_platforms'] = detected_platforms
        
        return updates

    def generate_response(self, user_id: str, user_message: str) -> Dict[str, Any]:
        """Enhanced response generation with interactive conversation flow"""
        self.last_activity[user_id] = time.time()
        
        # Initialize if new user
        if user_id not in self.conversation_contexts:
            initial_response = self.initialize_conversation(user_id)
            return {
                "response": initial_response,
                "context": self.conversation_contexts[user_id],
                "state": self.conversation_states[user_id],
                "is_complete": False
            }

        # Update context
        context = self.update_context_from_message(user_id, user_message)
        state = self.conversation_states[user_id]
        
        # State transitions
        missing_fields = self.get_missing_fields(context)
        
        if state == ConversationState.COLLECTING_CONTEXT and not missing_fields:
            state = ConversationState.GATHERING_INSIGHTS
            self.conversation_states[user_id] = state
        
        # Check if ready for campaign generation
        if (state == ConversationState.GATHERING_INSIGHTS and 
            context.competitors and 
            context.trending_keywords and 
            context.key_messages):
            state = ConversationState.READY_FOR_CAMPAIGN
            self.conversation_states[user_id] = state
        
        # Handle campaign creation request
        if (state == ConversationState.READY_FOR_CAMPAIGN and 
            self._should_create_campaign(user_message)):
            
            state = ConversationState.GENERATING_CAMPAIGN
            self.conversation_states[user_id] = state
            campaign_content = self.generate_campaign_content(user_id)
            
            return {
                "response": "🎉 **Campaign Generation Complete!**\n\nI've created a comprehensive marketing campaign tailored to your needs. Here are your deliverables:",
                "context": context,
                "state": state,
                "is_complete": True,
                "campaign_content": campaign_content
            }
        
        # Generate conversational response
        next_question, is_ready = self.get_next_question(context, state)
        
        if is_ready and state != ConversationState.READY_FOR_CAMPAIGN:
            response = next_question
        else:
            # Use AI for nuanced responses
            prompt = self._build_conversation_prompt(context, state, user_message, next_question)
            ai_response = self.ollama_client.chat(
                model=settings.ollama_model,
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': settings.temperature}
            )
            response = ai_response['message']['content']

        return {
            "response": response,
            "context": context,
            "state": state,
            "is_complete": False
        }

    def _build_conversation_prompt(self, context: UserContext, state: ConversationState, 
                                 user_message: str, next_question: str) -> str:
        """Build context-aware conversation prompt"""
        return f"""
        {self.system_prompt}

        Current Context:
        {context.json()}

        Conversation State: {state}
        User Message: "{user_message}"

        Next question to guide toward: {next_question}

        Your Response Should:
        1. Acknowledge the user's input naturally
        2. Guide them toward the next question organically
        3. Provide marketing insights when relevant
        4. Keep the conversation focused and productive
        5. Be concise but helpful

        Respond as a marketing expert:
        """

    def generate_campaign_content(self, user_id: str) -> Dict[str, Any]:
        """Generate comprehensive campaign deliverables"""
        context = self.conversation_contexts[user_id]
        
        campaign_prompt = f"""
        {self.system_prompt}

        Generate a COMPLETE marketing campaign based on this context:

        {context.json()}

        DELIVERABLES REQUIRED:

        1. CAMPAIGN STRATEGY OVERVIEW
        - Overall approach and positioning
        - Key differentiators
        - Success metrics

        2. AD COPY (for each specified platform)
        - Attention-grabbing headlines
        - Compelling body copy
        - Strong calls-to-action
        - Hashtags where relevant

        3. EMAIL DRAFTS
        - Welcome/announcement email
        - Educational/follow-up email
        - Promotional email
        - Complete with subject lines

        4. SOCIAL MEDIA CONTENT
        - 5-7 post ideas with full copy
        - Platform-specific formatting
        - Visual content suggestions

        5. CAMPAIGN TIMELINE
        - Phase 1: Preparation (Days 1-3)
        - Phase 2: Launch (Days 4-10)
        - Phase 3: Optimization (Days 11-30)

        Return as structured JSON with this exact format:
        {{
            "campaign_strategy": {{
                "overview": "2-3 paragraph strategy",
                "targeting": "Audience targeting approach",
                "positioning": "Brand positioning statement",
                "success_metrics": ["Metric 1", "Metric 2"]
            }},
            "ad_copy": {{
                "facebook": ["Headline 1", "Headline 2"],
                "instagram": ["Post 1", "Post 2"],
                "email": ["Subject: ...\\n\\nBody..."],
                "google_ads": ["Headline 1 | Headline 2"]
            }},
            "email_drafts": [
                "Subject: ...\\n\\nBody content...",
                "Subject: ...\\n\\nBody content..."
            ],
            "social_media_posts": [
                "Platform: Post content with hashtags",
                "Platform: Post content with hashtags"
            ],
            "content_calendar": {{
                "week_1": ["Task 1", "Task 2"],
                "week_2": ["Task 1", "Task 2"],
                "week_3": ["Task 1", "Task 2"],
                "week_4": ["Task 1", "Task 2"]
            }},
            "key_messaging": ["Message 1", "Message 2", "Message 3"]
        }}

        Make all content specific, actionable, and tailored to the context.
        """

        try:
            response = self.ollama_client.chat(
                model=settings.ollama_model,
                messages=[{'role': 'user', 'content': campaign_prompt}],
                options={'temperature': 0.7, 'num_predict': 4000}
            )
            
            content = response['message']['content']
            campaign_content = self._parse_ai_response(content)
            return campaign_content
            
        except Exception as e:
            print(f"Error generating campaign: {e}")
            return self._create_default_campaign()

    def _parse_ai_response(self, content: str) -> Dict[str, Any]:
        """Robust JSON parsing with multiple fallback strategies"""
        try:
            # Try direct JSON parsing first
            return json.loads(content)
        except json.JSONDecodeError:
            # Extract JSON from markdown or other formats
            json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
            
            # Fallback: create structured content
            return self._create_structured_campaign_from_text(content)

    def _create_default_campaign(self) -> Dict[str, Any]:
        """Default campaign structure"""
        return {
            "campaign_strategy": {
                "overview": "Data-driven marketing campaign focused on your target audience and business goals.",
                "targeting": "Precision targeting based on audience demographics and behaviors.",
                "positioning": "Clear market positioning highlighting unique value propositions.",
                "success_metrics": ["Engagement rate", "Conversion rate", "ROI", "Brand awareness"]
            },
            "ad_copy": {
                "facebook": ["Engaging Facebook ad copy tailored to your audience"],
                "instagram": ["Visual Instagram content with compelling captions"],
                "email": ["Professional email campaigns with clear CTAs"],
                "google_ads": ["High-converting Google Ads copy with relevant keywords"]
            },
            "email_drafts": [
                "Subject: Welcome to Our Campaign\n\nEngaging email content...",
                "Subject: Special Offer Inside\n\nCompelling follow-up content..."
            ],
            "social_media_posts": [
                "Engaging social media post with relevant hashtags",
                "Educational content about your industry",
                "Promotional post with clear call-to-action"
            ],
            "content_calendar": {
                "week_1": ["Platform setup", "Content creation", "Audience research"],
                "week_2": ["Campaign launch", "Initial promotions", "Engagement tracking"],
                "week_3": ["Performance analysis", "Content optimization", "A/B testing"],
                "week_4": ["Scale successful tactics", "Audience expansion", "ROI calculation"]
            },
            "key_messaging": [
                "Clear value proposition",
                "Compelling unique selling points", 
                "Strong call-to-action messaging"
            ]
        }

    def _create_structured_campaign_from_text(self, text: str) -> Dict[str, Any]:
        """Create structured campaign from unstructured text"""
        return self._create_default_campaign()

    def _should_create_campaign(self, user_message: str) -> bool:
        """Check if user wants to create campaign"""
        triggers = ['create campaign', 'yes', 'generate', 'make campaign', 'proceed', 'go ahead', 'ready', 'start']
        return any(trigger in user_message.lower() for trigger in triggers)

# Global service instance
marketing_ai_service = MarketingAIService()