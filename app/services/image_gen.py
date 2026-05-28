"""
Image generation service for Christian-themed images.
Note: Poe API doesn't provide direct image generation.
This service provides prompt preparation and safety checks.
For actual image generation, you can use DALL-E bot on Poe,
or integrate with external services like Stability AI.
"""
from typing import Dict, Optional
import base64
import asyncio
from io import BytesIO

from app.services.poe_client import PoeApi

from app.config import settings
from app.services.moderation import get_moderation_service
from app.prompts.system import IMAGE_PROMPT_TEMPLATE


class ImageGenerationService:
    """Service for generating Christian-themed images with safety checks."""
    
    def __init__(self):
        self.client = PoeApi(settings.groq_api_key)
        self.model = settings.llm_model
        self.moderation_service = get_moderation_service()
    
    def _generate_sync(self, prompt: str) -> str:
        """Generate response synchronously using Poe API."""
        try:
            response_text = ""
            for chunk in self.client.send_message(self.model, prompt):
                response_text = chunk["text"]
            return response_text.strip()
        except Exception as e:
            raise Exception(f"Poe API error: {str(e)}")
    
    async def _create_safe_prompt(self, user_request: str) -> str:
        """Transform user request into a safe, appropriate image prompt."""
        try:
            prompt = f"""You are an image prompt creator for a Christian AI assistant. 
Create detailed, reverent image prompts that:
- Are appropriate for all Christian audiences
- Maintain respect for sacred imagery
- Avoid any violent, disturbing, or disrespectful content
- Focus on beauty, peace, and spiritual themes
- Include artistic style guidance (e.g., "oil painting style", "soft lighting")

Output only the image generation prompt, nothing else.

{IMAGE_PROMPT_TEMPLATE.format(user_request=user_request)}"""
            
            response = await asyncio.to_thread(self._generate_sync, prompt)
            return response
        except Exception as e:
            # Fall back to a simple transformation
            return f"A beautiful, reverent Christian-themed image depicting: {user_request}. Peaceful, respectful artistic style with soft lighting."
    
    async def generate_image(
        self,
        user_request: str,
        size: str = "1024x1024",
        quality: str = "standard"
    ) -> Dict:
        """
        Generate a Christian-themed image based on user request.
        
        Args:
            user_request: User's description of desired image
            size: Image size (1024x1024, 1024x1792, or 1792x1024)
            quality: Image quality (standard or hd)
            
        Returns:
            Dict with image URL or error information
        """
        # Step 1: Check image request safety
        safety_check = await self.moderation_service.check_image_safety(user_request)
        
        if not safety_check["is_safe"]:
            # Return refusal with optional safe alternative
            response = {
                "success": False,
                "error": safety_check["refusal_message"],
                "safety_category": safety_check["category"]
            }
            
            if safety_check.get("safe_alternative"):
                response["suggested_alternative"] = safety_check["safe_alternative"]
            
            return response
        
        # Step 2: Create safe, enhanced prompt
        safe_prompt = await self._create_safe_prompt(user_request)
        
        # Step 3: Generate image
        # Note: Google's Imagen API requires specific access
        # For now, we return the prepared prompt for use with other services
        # You can integrate with Stability AI, Replicate, or request Imagen access
        
        try:
            # Try using Gemini's image generation if available
            # This requires google-generativeai with imagen support
            from google.generativeai import ImageGenerationModel
            
            imagen = ImageGenerationModel.from_pretrained(settings.image_model)
            response = imagen.generate_images(
                prompt=safe_prompt,
                number_of_images=1,
            )
            
            if response.images:
                # Save image and return URL/path
                import tempfile
                import os
                temp_dir = tempfile.gettempdir()
                image_path = os.path.join(temp_dir, f"christian_ai_image_{hash(safe_prompt)}.png")
                response.images[0].save(image_path)
                
                return {
                    "success": True,
                    "image_path": image_path,
                    "original_request": user_request,
                    "generated_prompt": safe_prompt
                }
            
        except ImportError:
            # Imagen not available, return prompt for external use
            return {
                "success": True,
                "image_url": None,
                "original_request": user_request,
                "generated_prompt": safe_prompt,
                "message": "Image prompt generated. Use this prompt with an image generation service like Stable Diffusion, Midjourney, or request Google Imagen API access.",
                "prompt_ready": True
            }
        except Exception as e:
            return {
                "success": True,
                "image_url": None,
                "original_request": user_request,
                "generated_prompt": safe_prompt,
                "message": f"Image prompt generated. Note: {str(e)}",
                "prompt_ready": True
            }
    
    async def generate_verse_illustration(
        self,
        verse_reference: str,
        verse_text: str
    ) -> Dict:
        """
        Generate an illustration for a specific Bible verse.
        
        Args:
            verse_reference: The verse reference (e.g., "Psalm 23:1")
            verse_text: The verse text
            
        Returns:
            Dict with image URL or error information
        """
        # Create a specific prompt for verse illustration
        prompt = f"Create a beautiful, reverent illustration for the Bible verse {verse_reference}: \"{verse_text}\". The image should capture the spiritual essence and meaning of this scripture."
        
        return await self.generate_image(prompt, quality="hd")
    
    def get_suggested_themes(self) -> list:
        """Get a list of suggested Christian image themes."""
        return [
            "A peaceful scene of prayer and meditation",
            "The beauty of God's creation in nature",
            "A warm church community gathering",
            "Light breaking through clouds (divine presence)",
            "A shepherd caring for sheep (Psalm 23)",
            "A peaceful garden scene (Garden of Eden)",
            "Hands folded in prayer",
            "A beautiful cross with sunrise",
            "The dove of peace (Holy Spirit)",
            "An open Bible with soft light",
            "A path through a forest (the narrow way)",
            "A lighthouse guiding ships (Christ the light)",
            "Seeds growing into plants (parable of the sower)",
            "A mustard seed growing into a tree",
            "Living water flowing (John 4)"
        ]


# Singleton instance
_image_service: Optional[ImageGenerationService] = None


def get_image_service() -> ImageGenerationService:
    """Get or create image generation service singleton."""
    global _image_service
    if _image_service is None:
        _image_service = ImageGenerationService()
    return _image_service
