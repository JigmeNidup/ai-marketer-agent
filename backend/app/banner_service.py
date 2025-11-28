
import os
import fal_client
import base64
import requests
from io import BytesIO
from typing import Dict

# No need to initialize a client instance anymore
# Make sure FAL_KEY environment variable is set

class FalBannerGenerator:
    def __init__(self):
        self.model_id = "fal-ai/flux/schnell"  # Using FLUX.1 [schnell] for speed

    def get_aspect_ratio_dimensions(self, aspect_ratio: str) -> tuple:
        """Map aspect ratio string to width and height."""
        ratios = {
            "1:1": (1024, 1024),
            "16:9": (1024, 576),
            "9:16": (576, 1024),
            "4:3": (1024, 768),
            "3:4": (768, 1024),
        }
        return ratios.get(aspect_ratio, (1024, 1024))

    def create_marketing_prompt(self, context: Dict) -> str:
        """Create an optimized prompt from campaign context."""
        product_info = context.get('product_details', 'our product/service')
        target_audience = context.get('target_audience', 'target customers')
        brand_tone = context.get('brand_tone', 'professional')
        
        prompt = f"Professional marketing banner for {product_info}, target audience: {target_audience}, brand tone: {brand_tone}"
        
        if context.get('key_messages'):
            key_msg = context['key_messages'][0]
            prompt += f", key message: {key_msg}"
        
        # Add style guidance
        style_map = {
            "professional": "clean corporate design, modern layout, professional typography",
            "casual": "friendly design, warm colors, relatable imagery",
            "funny": "playful design, bright colors, engaging composition",
            "inspirational": "uplifting design, motivational imagery, elegant composition",
            "authoritative": "bold design, strong typography, premium aesthetic"
        }
        
        prompt += ". " + style_map.get(str(brand_tone).lower(), style_map["professional"])
        prompt += ", high quality, detailed, professional photography"
        
        return prompt

    def generate_campaign_banner(self, context: Dict, aspect_ratio: str = "16:9") -> Dict:
        """Generate a campaign banner using Fal.ai."""
        try:
            prompt = self.create_marketing_prompt(context)
            width, height = self.get_aspect_ratio_dimensions(aspect_ratio)
            
            print(f"🎨 Generating {width}x{height} banner with Fal.ai...")
            
            # Call Fal.ai API using the new syntax
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
            
            # Download the image and convert to base64 for your API response
            image_response = requests.get(image_url)
            image_data = base64.b64encode(image_response.content).decode()
            
            return {
                "success": True,
                "image_data": image_data,
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "dimensions": f"{width}x{height}",
                "model": "FLUX.1 [schnell] via Fal.ai",
                "message": "Banner generated successfully with Fal.ai"
            }
            
        except Exception as e:
            error_msg = f"Fal.ai generation error: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "message": "Failed to generate banner"
            }

# Global instance
banner_generator = FalBannerGenerator()