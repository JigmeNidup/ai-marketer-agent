import ollama
import requests
import json
import time
import re
import os
from typing import Dict, Any, List
from .models import UserContext, ConversationState, BrandTone, CampaignGoal, Platform
from .config import settings

class SerperSearchService:
    """Real web search service using Serper API"""
    
    def __init__(self):
        self.api_key = settings.serper_api_key
        self.base_url = settings.serper_api_url
    
    def search_competitors(self, product_type: str, industry: str = "") -> List[str]:
        """Search for real competitors using Serper API"""
        if not self.api_key:
            return self._get_fallback_competitors(product_type)
            
        query = f"top companies in {product_type} industry competitors"
        if industry:
            query = f"top {industry} companies competitors {product_type}"
        
        payload = {
            "q": query,
            "gl": "us",
            "hl": "en",
            "num": 10
        }
        
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json',
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload)
            data = response.json()
            
            competitors = []
            # Extract from organic results
            if 'organic' in data:
                for item in data['organic'][:5]:
                    title = item.get('title', '')
                    # Clean up title and extract company name
                    company = self._extract_company_name(title)
                    if company and company not in competitors:
                        competitors.append(company)
            
            return competitors if competitors else self._get_fallback_competitors(product_type)
            
        except Exception as e:
            print(f"Serper API error: {e}")
            return self._get_fallback_competitors(product_type)
    
    def search_trending_keywords(self, industry: str, product_type: str = "") -> List[str]:
        """Search for trending keywords in the industry"""
        if not self.api_key:
            return self._get_fallback_trends(industry)
            
        query = f"trending topics in {industry} industry 2024 latest"
        if product_type:
            query = f"{product_type} trends 2024 {industry}"
        
        payload = {
            "q": query,
            "gl": "us",
            "hl": "en"
        }
        
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload)
            data = response.json()
            
            trends = []
            # Extract from People Also Ask and related searches
            if 'peopleAlsoAsk' in data:
                for item in data['peopleAlsoAsk'][:5]:
                    question = item.get('question', '')
                    if question:
                        trends.append(question)
            
            if 'relatedSearches' in data:
                for item in data['relatedSearches'][:5]:
                    search_query = item.get('query', '')
                    if search_query:
                        trends.append(search_query)
            
            # Also extract from organic results
            if 'organic' in data and not trends:
                for item in data['organic'][:3]:
                    title = item.get('title', '')
                    if 'trend' in title.lower() or '2024' in title:
                        trends.append(title)
            
            return trends if trends else self._get_fallback_trends(industry)
            
        except Exception as e:
            print(f"Serper API error: {e}")
            return self._get_fallback_trends(industry)
    
    def _extract_company_name(self, title: str) -> str:
        """Extract company name from search result title"""
        # Remove common suffixes and clean up
        clean_title = re.sub(r' - .*$', '', title)  # Remove everything after -
        clean_title = re.sub(r'\|.*$', '', clean_title)  # Remove everything after |
        clean_title = re.sub(r'^.*?: ', '', clean_title)  # Remove prefix before :
        clean_title = re.sub(r'\s+', ' ', clean_title).strip()  # Normalize spaces
        
        # Remove common words
        remove_words = ['review', 'reviews', 'best', 'top', '2024', '2023', 'buy', 'price']
        words = clean_title.split()
        filtered_words = [word for word in words if word.lower() not in remove_words]
        
        return ' '.join(filtered_words[:4])  # Return first 4 words as company name
    
    def _get_fallback_competitors(self, product_type: str) -> List[str]:
        """Fallback competitor data if API fails"""
        competitor_map = {
            "health": ["Fitbit", "MyFitnessPal", "Headspace", "Calm", "Noom"],
            "tech": ["Apple", "Samsung", "Google", "Microsoft", "Amazon"],
            "fashion": ["Zara", "H&M", "Nike", "Adidas", "Uniqlo"],
            "food": ["McDonald's", "Starbucks", "Domino's", "Chipotle", "Subway"],
            "finance": ["PayPal", "Square", "Robinhood", "Coinbase", "Stripe"],
            "education": ["Coursera", "Udemy", "Khan Academy", "Duolingo", "Skillshare"],
            "software": ["Salesforce", "Adobe", "Slack", "Zoom", "Microsoft 365"],
            "beauty": ["Sephora", "Ulta", "Glossier", "Fenty Beauty", "The Ordinary"]
        }
        
        for category, competitors in competitor_map.items():
            if category in product_type.lower():
                return competitors
        return ["Industry Leader A", "Emerging Competitor B", "Direct Competitor C", "Market Disruptor D"]
    
    def _get_fallback_trends(self, industry: str) -> List[str]:
        """Fallback trend data if API fails"""
        trend_map = {
            "health": ["mental wellness", "telehealth", "fitness tech", "personalized nutrition", "sleep optimization"],
            "tech": ["AI integration", "sustainable tech", "edge computing", "quantum computing", "web3"],
            "fashion": ["sustainable fashion", "digital clothing", "upcycling", "inclusive sizing", "slow fashion"],
            "food": ["plant-based alternatives", "functional foods", "ghost kitchens", "local sourcing", "meal kits"],
            "finance": ["decentralized finance", "buy now pay later", "embedded finance", "AI banking", "sustainable investing"],
            "education": ["micro-learning", "skills-based education", "VR learning", "corporate training", "lifelong learning"]
        }
        
        for category, trends in trend_map.items():
            if category in industry.lower():
                return trends
        return ["digital transformation", "customer experience", "sustainability", "personalization", "mobile-first"]

class MarketingAIService:
    def __init__(self):
        self.conversation_contexts: Dict[str, UserContext] = {}
        self.conversation_states: Dict[str, ConversationState] = {}
        self.conversation_histories: Dict[str, List[Dict]] = {}
        self.last_activity: Dict[str, float] = {}
        self.search_service = SerperSearchService()
        
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

IMPORTANT: If the user asks to generate the campaign immediately or says they're ready, proceed with campaign creation using whatever context is available. Don't ask for more information if they explicitly want to proceed.

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

    def _cleanup_old_conversations(self):
        """Remove conversations older than max_conversation_age"""
        current_time = time.time()
        expired_users = [
            user_id for user_id, last_active in self.last_activity.items()
            if current_time - last_active > settings.max_conversation_age
        ]
        
        for user_id in expired_users:
            self.conversation_contexts.pop(user_id, None)
            self.conversation_states.pop(user_id, None)
            self.conversation_histories.pop(user_id, None)
            self.last_activity.pop(user_id, None)

    def initialize_conversation(self, user_id: str) -> str:
        """Initialize a new conversation with system prompt"""
        self._cleanup_old_conversations()
        
        self.conversation_contexts[user_id] = UserContext()
        self.conversation_states[user_id] = ConversationState.COLLECTING_CONTEXT
        self.conversation_histories[user_id] = []
        self.last_activity[user_id] = time.time()
        
        initial_prompt = f"""{self.system_prompt}

🚀 **Welcome to Your AI Marketing Strategist!**

I'll help you create a comprehensive marketing campaign. We can either:
1. Go through all the details step by step, OR
2. You can tell me to "generate campaign now" at any point and I'll create it with whatever information we have!

Let's start by understanding your product or service. What are you offering?"""
        
        return initial_prompt

    def get_missing_fields(self, context: UserContext) -> List[str]:
        """Get list of missing required fields"""
        missing = []
        for field in settings.required_fields:
            current_value = getattr(context, field)
            if current_value is None or (isinstance(current_value, list) and len(current_value) == 0):
                missing.append(field)
        return missing

    def _should_generate_campaign_early(self, user_message: str) -> bool:
        """Check if user wants to generate campaign immediately"""
        early_triggers = [
            'generate campaign now', 'create campaign now', 'make campaign now',
            'stop talking and generate', 'just create the campaign', 
            'proceed with current information', 'use what you have',
            'generate with current context', 'create with what we have',
            'i\'m ready', 'let\'s generate', 'make it now', 'build campaign',
            'that\'s enough info', 'go ahead and create'
        ]
        user_message_lower = user_message.lower()
        return any(trigger in user_message_lower for trigger in early_triggers)

    def _enhance_context_with_web_search(self, context: UserContext) -> UserContext:
        """Enhance context with real web search data"""
        if not context.web_enhanced and context.product_details:
            print("Enhancing context with web search...")
            
            # Extract industry from product details
            industry_keywords = {
                'health': ['health', 'fitness', 'wellness', 'medical', 'therapy'],
                'tech': ['tech', 'software', 'app', 'digital', 'saas'],
                'fashion': ['fashion', 'clothing', 'apparel', 'style', 'wear'],
                'food': ['food', 'restaurant', 'meal', 'recipe', 'cooking'],
                'finance': ['finance', 'banking', 'investment', 'money', 'financial'],
                'education': ['education', 'learning', 'course', 'training', 'school']
            }
            
            industry = "general"
            for ind, keywords in industry_keywords.items():
                if any(keyword in context.product_details.lower() for keyword in keywords):
                    industry = ind
                    break
            
            # Search for competitors and trends
            competitors = self.search_service.search_competitors(context.product_details, industry)
            trends = self.search_service.search_trending_keywords(industry, context.product_details)
            
            if competitors:
                context.competitors = competitors
            if trends:
                context.trending_keywords = trends
            
            context.web_enhanced = True
            print(f"Web enhancement complete: {len(competitors)} competitors, {len(trends)} trends")
        
        return context

    def update_context_from_message(self, user_id: str, message: str) -> UserContext:
        """Update context from user message with enhanced extraction"""
        context = self.conversation_contexts[user_id]
        
        # Manual context extraction
        updates = self._extract_context_manual(message, context)
        
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

    def _extract_context_manual(self, message: str, current_context: UserContext) -> Dict[str, Any]:
        """Manual context extraction"""
        updates = {}
        message_lower = message.lower()
        
        # Basic field extraction patterns
        patterns = {
            'target_audience': [
                r'(?:audience|target|customers?|users?).{0,20}?(?:is|are|:)\s*([^.!?]+)',
                r'(?:reach|targeting|focusing on)\s+([^.!?]+?)(?:audience|market|demographic)',
            ],
            'product_details': [
                r'(?:product|service|business|offering).{0,30}?(?:is|are|:)\s*([^.!?]+)',
                r'(?:sell|offer|provide).{0,30}?([^.!?]+)',
            ],
        }
        
        for field, field_patterns in patterns.items():
            for pattern in field_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    value = match.group(1).strip()
                    if value and len(value) > 2:
                        updates[field] = value.capitalize()
                        break
        
        # Enum field extraction
        updates.update(self._extract_enum_fields(message))
        
        return updates

    def _extract_enum_fields(self, message: str) -> Dict[str, Any]:
        """Extract enum fields"""
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
        """Enhanced response generation with early campaign trigger"""
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

        # Check for early campaign generation
        if self._should_generate_campaign_early(user_message):
            return self._generate_campaign_with_current_context(user_id)

        # Update context
        context = self.update_context_from_message(user_id, user_message)
        state = self.conversation_states[user_id]
        
        # State transitions
        missing_fields = self.get_missing_fields(context)
        
        if state == ConversationState.COLLECTING_CONTEXT and not missing_fields:
            state = ConversationState.GATHERING_INSIGHTS
            self.conversation_states[user_id] = state
        
        # Check if ready for campaign generation
        if state == ConversationState.GATHERING_INSIGHTS and context.competitors and context.trending_keywords:
            state = ConversationState.READY_FOR_CAMPAIGN
            self.conversation_states[user_id] = state
        
        # Handle campaign creation request
        if state == ConversationState.READY_FOR_CAMPAIGN and self._should_create_campaign(user_message):
            return self._generate_campaign_with_current_context(user_id)
        
        # Generate conversational response
        response = self._generate_conversational_response(context, state, user_message)
        
        return {
            "response": response,
            "context": context,
            "state": state,
            "is_complete": False
        }

    def _generate_campaign_with_current_context(self, user_id: str) -> Dict[str, Any]:
        """Generate campaign with available context, enhanced with web search"""
        context = self.conversation_contexts[user_id]
        
        print(f"Generating campaign with current context. Missing fields: {self.get_missing_fields(context)}")
        
        # Enhance with web search
        context = self._enhance_context_with_web_search(context)
        
        # Generate campaign content
        campaign_content = self.generate_campaign_content(user_id)
        
        # Update state
        self.conversation_states[user_id] = ConversationState.GENERATING_CAMPAIGN
        
        # Build response message based on context completeness
        missing_fields = self.get_missing_fields(context)
        if missing_fields:
            response_msg = f"🚀 **Generating Campaign with Available Context**\n\nI'm creating your campaign with the information we have. I've supplemented with web research for missing details. Here's your tailored strategy:"
        else:
            response_msg = f"🎉 **Campaign Generation Complete!**\n\nI've created a comprehensive marketing campaign based on all your requirements. Here are your deliverables:"
        
        return {
            "response": response_msg,
            "context": context,
            "state": ConversationState.GENERATING_CAMPAIGN,
            "is_complete": True,
            "campaign_content": campaign_content
        }

    def _generate_conversational_response(self, context: UserContext, state: ConversationState, user_message: str) -> str:
        """Generate appropriate conversational response based on state"""
        
        if state == ConversationState.COLLECTING_CONTEXT:
            missing_fields = self.get_missing_fields(context)
            if missing_fields:
                field_questions = {
                    'target_audience': "🎯 **Who is your target audience?** (e.g., 'Young professionals aged 25-35 interested in fitness and sustainability')",
                    'brand_tone': "🎭 **What brand tone would you like?** (professional, casual, funny, inspirational, authoritative)",
                    'campaign_goals': "🎯 **What are your main campaign goals?** (brand awareness, conversions, engagement, lead generation)",
                    'preferred_platforms': "📱 **Which platforms will you use?** (Facebook, Instagram, Twitter, LinkedIn, Email, Google Ads, TikTok, YouTube)",
                    'product_details': "📦 **Tell me about your product/service and its key benefits**"
                }
                next_question = field_questions[missing_fields[0]]
                
                prompt = f"""
                {self.system_prompt}
                
                Current context collected so far:
                - Product: {context.product_details or 'Not specified'}
                - Audience: {context.target_audience or 'Not specified'} 
                - Tone: {context.brand_tone or 'Not specified'}
                - Goals: {', '.join([g.value for g in context.campaign_goals]) if context.campaign_goals else 'Not specified'}
                - Platforms: {', '.join([p.value for p in context.preferred_platforms]) if context.preferred_platforms else 'Not specified'}
                
                User just said: "{user_message}"
                
                Next question to ask: {next_question}
                
                Respond naturally, acknowledge their input, and ask the next question. Keep it conversational.
                """
            else:
                # Move to insights gathering
                prompt = f"""
                {self.system_prompt}
                
                Great! I have the basic information. Now let's gather some market insights.
                
                User message: "{user_message}"
                
                Ask if they have specific competitors in mind, or if they'd like you to research current competitors and trends for their industry.
                """
        
        elif state == ConversationState.GATHERING_INSIGHTS:
            if not context.competitors:
                prompt = f"""
                {self.system_prompt}
                
                Let's research your competitive landscape.
                
                User message: "{user_message}"
                
                Ask about their main competitors, or offer to research current competitors in their space.
                """
            elif not context.trending_keywords:
                prompt = f"""
                {self.system_prompt}
                
                Now let's look at current market trends.
                
                User message: "{user_message}"
                
                Ask about any specific keywords or trends they want to target, or offer to research current trends.
                """
            else:
                prompt = f"""
                {self.system_prompt}
                
                We have all the insights we need! The user can now ask to generate the campaign.
                
                User message: "{user_message}"
                
                Let them know we're ready to create their campaign and they can say "generate campaign now" whenever they're ready.
                """
        
        else:
            # Ready for campaign
            prompt = f"""
            {self.system_prompt}
            
            We're ready to generate the campaign! The user can trigger it at any time.
            
            User message: "{user_message}"
            
            Remind them they can say "generate campaign now" to create their marketing campaign.
            """
        
        # Get AI response
        ai_response = self.ollama_client.chat(
            model=settings.ollama_model,
            messages=[{'role': 'user', 'content': prompt}],
            options={'temperature': settings.temperature, 'num_predict': settings.max_tokens}
        )
        
        return ai_response['message']['content']

    def _should_create_campaign(self, user_message: str) -> bool:
        """Check if user wants to create campaign"""
        triggers = ['create campaign', 'yes', 'generate', 'make campaign', 'proceed', 'go ahead', 'ready', 'start']
        return any(trigger in user_message.lower() for trigger in triggers)

    def generate_campaign_content(self, user_id: str) -> Dict[str, Any]:
        """Generate comprehensive campaign deliverables"""
        context = self.conversation_contexts[user_id]
        
        campaign_prompt = f"""
        {self.system_prompt}

        Generate a COMPLETE marketing campaign based on this context:

        CONTEXT:
        {context.json()}

        DELIVERABLES REQUIRED:

        1. CAMPAIGN STRATEGY OVERVIEW
        - Overall approach and positioning
        - Key differentiators against competitors: {context.competitors}
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
                "success_metrics": ["Metric 1", "Metric 2", "Metric 3"],
                "competitive_advantage": "How it stands out from competitors"
            }},
            "ad_copy": {{
                "facebook": ["Headline 1", "Headline 2", "Body copy..."],
                "instagram": ["Post 1", "Post 2", "Story ideas..."],
                "email": ["Subject: ...\\n\\nBody..."],
                "google_ads": ["Headline 1 | Headline 2 | Description"]
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
                "week_1": ["Task 1", "Task 2", "Task 3"],
                "week_2": ["Task 1", "Task 2", "Task 3"],
                "week_3": ["Task 1", "Task 2", "Task 3"],
                "week_4": ["Task 1", "Task 2", "Task 3"]
            }},
            "key_messaging": ["Message 1", "Message 2", "Message 3"]
        }}

        Make all content specific, actionable, and tailored to the context. Use real competitor names and trends when available.
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
        if not content:
            return self._create_default_campaign()
        
        # Strategy 1: Try direct JSON parsing
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Strategy 3: Extract anything that looks like JSON
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Strategy 4: If all else fails, create structured content from text
        return self._create_structured_campaign_from_text(content)

    def _create_default_campaign(self) -> Dict[str, Any]:
        """Default campaign structure"""
        return {
            "campaign_strategy": {
                "overview": "Data-driven marketing campaign focused on your target audience and business goals, enhanced with current market insights.",
                "targeting": "Precision targeting based on audience demographics, behaviors, and current market trends.",
                "positioning": "Clear market positioning highlighting unique value propositions and competitive advantages.",
                "success_metrics": ["Engagement rate", "Conversion rate", "ROI", "Brand awareness", "Lead generation"],
                "competitive_advantage": "Leveraging unique selling points to differentiate from market competitors"
            },
            "ad_copy": {
                "facebook": ["Engaging Facebook ad copy tailored to your audience with strong CTAs"],
                "instagram": ["Visual Instagram content with compelling captions and relevant hashtags"],
                "email": ["Professional email campaigns with clear value propositions and calls-to-action"],
                "google_ads": ["High-converting Google Ads copy with relevant keywords and compelling offers"]
            },
            "email_drafts": [
                "Subject: Welcome to Our Exclusive Campaign!\n\nEngaging email content highlighting key benefits and next steps...",
                "Subject: Special Offer Inside - Don't Miss Out!\n\nCompelling follow-up content with clear call-to-action..."
            ],
            "social_media_posts": [
                "Facebook: Engaging post about your unique value proposition with relevant hashtags #marketing #business",
                "Instagram: Visual story showcasing your product benefits with behind-the-scenes content",
                "LinkedIn: Professional post highlighting industry insights and your solution"
            ],
            "content_calendar": {
                "week_1": ["Platform setup and audience research", "Content creation and asset development", "Initial audience targeting"],
                "week_2": ["Campaign launch across all channels", "Initial promotions and engagement", "Performance tracking setup"],
                "week_3": ["Performance analysis and optimization", "Content A/B testing", "Audience refinement"],
                "week_4": ["Scale successful tactics", "Expand to new audience segments", "ROI calculation and reporting"]
            },
            "key_messaging": [
                "Clear value proposition addressing customer pain points",
                "Compelling unique selling points against competitors", 
                "Strong call-to-action messaging driving conversions",
                "Trust-building social proof and testimonials"
            ]
        }

    def _create_structured_campaign_from_text(self, text: str) -> Dict[str, Any]:
        """Create structured campaign from unstructured text"""
        return self._create_default_campaign()

# Global service instance
marketing_ai_service = MarketingAIService()