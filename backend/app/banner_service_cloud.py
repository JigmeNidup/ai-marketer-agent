import os
import fal_client
import base64
import requests
from io import BytesIO
from typing import Dict, List, Any
import time

class FalBannerGenerator:
    def __init__(self):
        self.model_id = "fal-ai/flux/schnell"  # Using FLUX.1 [schnell] for speed
        self.platform_aspect_ratios = {
            "facebook": "1:1",
            "instagram": "1:1", 
            "instagram_stories": "9:16",
            "twitter": "16:9",
            "linkedin": "1:1",
            "youtube": "16:9",
            "tiktok": "9:16",
            "pinterest": "2:3",
            "website": "16:9"
        }

    def get_aspect_ratio_dimensions(self, aspect_ratio: str) -> tuple:
        """Map aspect ratio string to width and height."""
        ratios = {
            "1:1": (1024, 1024),
            "16:9": (1024, 576),
            "9:16": (576, 1024),
            "4:3": (1024, 768),
            "3:4": (768, 1024),
            "2:3": (682, 1024),
        }
        return ratios.get(aspect_ratio, (1024, 1024))

    def create_marketing_prompt(self, context: Dict, platform: str = "general") -> str:
        """Create an optimized prompt from campaign context."""
        product_info = context.get('product_details', 'our product/service')
        target_audience = context.get('target_audience', 'target customers')
        brand_tone = context.get('brand_tone', 'professional')
        campaign_goals = context.get('campaign_goals', [])
        
        # Base prompt
        prompt_parts = [f"Professional marketing banner for {product_info}"]
        
        # Add audience context
        prompt_parts.append(f"targeting {target_audience}")
        
        # Add platform-specific optimization
        platform_prompts = {
            "facebook": "Facebook ad banner, optimized for news feed",
            "instagram": "Instagram post, visually appealing and shareable",
            "instagram_stories": "Instagram story, vertical format, engaging",
            "twitter": "Twitter header or promoted post banner",
            "linkedin": "LinkedIn professional banner, corporate style",
            "youtube": "YouTube channel art or video thumbnail",
            "tiktok": "TikTok video thumbnail, trendy and eye-catching",
            "pinterest": "Pinterest pin, inspirational and detailed",
            "website": "Website header banner, professional and clean"
        }
        
        platform_prompt = platform_prompts.get(platform, "digital marketing banner")
        prompt_parts.append(platform_prompt)
        
        # Add brand tone styling
        style_map = {
            "professional": "clean corporate design, modern layout, professional typography, sophisticated",
            "casual": "friendly design, warm colors, relatable imagery, approachable",
            "funny": "playful design, bright colors, engaging composition, humorous elements",
            "inspirational": "uplifting design, motivational imagery, elegant composition, inspiring",
            "authoritative": "bold design, strong typography, premium aesthetic, trustworthy"
        }
        
        tone_style = style_map.get(str(brand_tone).lower(), style_map["professional"])
        prompt_parts.append(tone_style)
        
        # Add campaign goal context
        if campaign_goals:
            goals_text = ", ".join([goal if isinstance(goal, str) else goal.value for goal in campaign_goals])
            prompt_parts.append(f"campaign goals: {goals_text}")
        
        # Add key messages if available
        if context.get('key_messages'):
            key_msg = context['key_messages'][0]
            prompt_parts.append(f"key message: {key_msg}")
        
        # Add quality and style enhancements
        prompt_parts.extend([
            "high quality marketing design",
            "professional photography style",
            "excellent composition",
            "vibrant colors",
            "clear typography",
            "no text overlay needed",
            "marketing and advertising style"
        ])
        
        return ", ".join(prompt_parts)

    def generate_campaign_banner(self, context: Dict, aspect_ratio: str = "16:9", platform: str = "general") -> Dict:
        """Generate a campaign banner using Fal.ai."""
        try:
            prompt = self.create_marketing_prompt(context, platform)
            width, height = self.get_aspect_ratio_dimensions(aspect_ratio)
            
            print(f"🎨 Generating {width}x{height} banner for {platform} with Fal.ai...")
            print(f"📝 Prompt: {prompt}")
            
            # Call Fal.ai API
            result = fal_client.run(
                self.model_id,
                arguments={
                    "prompt": prompt,
                    "image_size": {"width": width, "height": height},
                    "num_inference_steps": 4,  # Optimal for FLUX.1 [schnell]
                    "enable_safety_checker": True,
                }
            )
            
            # The image URL is in the result
            image_url = result["images"][0]["url"]
            
            # Download the image and convert to base64 for API response
            image_response = requests.get(image_url)
            if image_response.status_code != 200:
                raise Exception(f"Failed to download image from Fal.ai: {image_response.status_code}")
                
            image_data = base64.b64encode(image_response.content).decode('utf-8')
            
            return {
                "success": True,
                "image_data": image_data,
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "dimensions": f"{width}x{height}",
                "platform": platform,
                "description": f"Marketing banner for {platform}",
                "model": "FLUX.1 [schnell] via Fal.ai",
                "message": "Banner generated successfully"
            }
            
        except Exception as e:
            error_msg = f"Fal.ai generation error: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "message": "Failed to generate banner",
                "platform": platform,
                "aspect_ratio": aspect_ratio
            }

    def generate_multiple_platform_banners(self, context: Dict) -> Dict[str, Dict]:
        """Generate banners for multiple platforms at once."""
        platforms_to_generate = [
            ("facebook", "1:1"),
            ("instagram", "1:1"),
            ("instagram_stories", "9:16"), 
            ("twitter", "16:9"),
            ("linkedin", "1:1"),
            ("website", "16:9")
        ]
        
        results = {}
        
        for platform, aspect_ratio in platforms_to_generate:
            print(f"🔄 Generating banner for {platform}...")
            
            result = self.generate_campaign_banner(
                context=context,
                aspect_ratio=aspect_ratio,
                platform=platform
            )
            
            results[platform] = result
            
            # Small delay to avoid rate limiting
            time.sleep(1)
        
        return results

    def generate_platform_specific_banner(self, context: Dict, platform: str) -> Dict:
        """Generate a banner optimized for a specific platform."""
        aspect_ratio = self.platform_aspect_ratios.get(platform, "16:9")
        return self.generate_campaign_banner(context, aspect_ratio, platform)

    def validate_context(self, context: Dict) -> bool:
        """Validate that context has minimum required information."""
        required_fields = ['product_details', 'target_audience']
        
        for field in required_fields:
            if not context.get(field):
                return False
                
        return True

    def get_supported_platforms(self) -> List[Dict[str, str]]:
        """Get list of supported platforms and their aspect ratios."""
        return [
            {"platform": platform, "aspect_ratio": ratio}
            for platform, ratio in self.platform_aspect_ratios.items()
        ]

# Global instance
banner_generator = FalBannerGenerator()