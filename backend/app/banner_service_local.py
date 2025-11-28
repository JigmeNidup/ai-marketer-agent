from diffusers import AutoPipelineForText2Image
import torch
import base64
from io import BytesIO
from typing import Dict, List
import time

class MarketingBannerGenerator:
    def __init__(self, model_name: str = "stabilityai/sdxl-turbo"):
        """
        Initialize with SDXL-Turbo - optimized for 1-4 step generation.
        """
        self.model_name = model_name
        self.setup_device()
        self.load_pipeline()
        
    def setup_device(self):
        """Setup computing device - SDXL-Turbo works great on CPU"""
        if torch.cuda.is_available():
            self.device = "cuda"
            self.torch_dtype = torch.float16
            print("🚀 Using GPU for SDXL-Turbo")
        else:
            self.device = "cpu" 
            self.torch_dtype = torch.float32
            print("🚀 Using CPU for SDXL-Turbo - Fast generation expected!")
        
    def load_pipeline(self):
        """Load the SDXL-Turbo pipeline"""
        try:
            print("📥 Loading SDXL-Turbo model...")
            
            # SDXL-Turbo uses a specific pipeline
            self.pipe = AutoPipelineForText2Image.from_pretrained(
                self.model_name,
                torch_dtype=self.torch_dtype,
                variant="fp16",
            )
            self.pipe = self.pipe.to(self.device)
            
            print("✅ SDXL-Turbo loaded successfully!")
            
        except Exception as e:
            print(f"❌ Error loading SDXL-Turbo: {e}")
            raise

    def get_aspect_ratios(self):
        """Get aspect ratios optimized for SDXL-Turbo"""
        return {
            "1:1": (512, 512),      # Square - Instagram posts
            "16:9": (768, 432),     # Widescreen - Website banners
            "9:16": (432, 768),     # Vertical - Instagram stories
            "4:3": (640, 480),      # Traditional - Tablet displays
            "3:4": (480, 640),      # Vertical traditional
        }

    def create_marketing_prompt(self, context: Dict) -> str:
        """Create optimized prompt for banner generation with SDXL-Turbo"""
        product_info = context.get('product_details', 'our product/service')
        target_audience = context.get('target_audience', 'target customers')
        brand_tone = context.get('brand_tone', 'professional')
        
        # Core prompt construction - SDXL-Turbo responds well to clear, concise prompts
        prompt = f"Professional marketing banner for {product_info}, target audience: {target_audience}"
        
        # Add key messaging
        if context.get('key_messages'):
            key_msg = context['key_messages'][0]
            prompt += f", message: {key_msg}"
        
        # Style guidance optimized for SDXL-Turbo
        style_map = {
            "professional": "clean corporate design, modern layout, professional typography, business aesthetic, high quality",
            "casual": "friendly design, warm colors, relatable imagery, approachable, authentic",
            "funny": "playful design, bright colors, engaging composition, humorous, lively",
            "inspirational": "uplifting design, motivational imagery, elegant composition, inspiring, aspirational",
            "authoritative": "bold design, strong typography, premium aesthetic, expert, trustworthy"
        }
        
        prompt += ". " + style_map.get(str(brand_tone).lower(), style_map["professional"])
        
        return prompt

    def generate_campaign_banner(self, context: Dict, aspect_ratio: str = "16:9") -> Dict:
        """Generate campaign banner using SDXL-Turbo (1-4 steps)"""
        try:
            prompt = self.create_marketing_prompt(context)
            aspect_ratios = self.get_aspect_ratios()
            width, height = aspect_ratios.get(aspect_ratio, (768, 432))
            
            print(f"🎨 Generating {width}x{height} banner with SDXL-Turbo...")
            start_time = time.time()
            
            # SDXL-Turbo is optimized for 1-4 steps with guidance_scale=0.0
            with torch.no_grad():
                image = self.pipe(
                    prompt=prompt,
                    num_inference_steps=2,      # 1-4 steps recommended for SDXL-Turbo
                    guidance_scale=0.0,         # Classifier-free guidance disabled for turbo
                    width=width,
                    height=height,
                    generator=torch.Generator(device=self.device).manual_seed(int(time.time()))
                ).images[0]
            
            generation_time = time.time() - start_time
            print(f"✅ Banner generated in {generation_time:.2f} seconds!")
            
            # Convert to base64
            buffered = BytesIO()
            image.save(buffered, format="JPEG", quality=90, optimize=True)
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            return {
                "success": True,
                "image_data": img_str,
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "dimensions": f"{width}x{height}",
                "generation_time": f"{generation_time:.2f}s",
                "model": "SDXL-Turbo",
                "message": f"Banner generated in {generation_time:.2f} seconds with SDXL-Turbo"
            }
            
        except Exception as e:
            error_msg = f"SDXL-Turbo generation error: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "message": "Failed to generate banner"
            }

    def generate_multiple_platform_banners(self, context: Dict) -> Dict:
        """Generate banners optimized for different platforms"""
        
        platform_configs = {
            "facebook": {"aspect_ratio": "16:9", "description": "Facebook cover photo"},
            "instagram_post": {"aspect_ratio": "1:1", "description": "Instagram square post"},
            "instagram_story": {"aspect_ratio": "9:16", "description": "Instagram story"},
            "twitter": {"aspect_ratio": "16:9", "description": "Twitter header"},
            "linkedin": {"aspect_ratio": "16:9", "description": "LinkedIn company banner"},
            "website": {"aspect_ratio": "16:9", "description": "Website header"}
        }
        
        results = {}
        successful_generations = 0
        
        for platform, config in platform_configs.items():
            print(f"🔄 Generating {platform} banner...")
            
            try:
                result = self.generate_campaign_banner(context, config["aspect_ratio"])
                result["platform"] = platform
                result["description"] = config["description"]
                
                results[platform] = result
                
                if result["success"]:
                    successful_generations += 1
                
                # Small delay between generations to prevent resource overload
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Failed to generate {platform} banner: {e}")
                results[platform] = {
                    "success": False,
                    "platform": platform,
                    "error": str(e),
                    "message": f"Failed to generate {platform} banner"
                }
        
        print(f"📊 Generation Summary: {successful_generations}/{len(platform_configs)} successful")
        
        return results

# Global banner generator instance
banner_generator = MarketingBannerGenerator()