"""
Image generation API routes.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

from app.services.image_gen import get_image_service

router = APIRouter()


class ImageRequest(BaseModel):
    """Request model for image generation."""
    prompt: str = Field(..., min_length=1, max_length=1000)
    size: str = Field(default="1024x1024", pattern="^(1024x1024|1024x1792|1792x1024)$")
    quality: str = Field(default="standard", pattern="^(standard|hd)$")


class VerseIllustrationRequest(BaseModel):
    """Request model for verse illustration."""
    verse_reference: str = Field(..., min_length=1, max_length=100)
    verse_text: str = Field(..., min_length=1, max_length=500)


class ImageResponse(BaseModel):
    """Response model for image generation."""
    success: bool
    image_url: Optional[str] = None
    error: Optional[str] = None
    generated_prompt: Optional[str] = None
    suggested_alternative: Optional[str] = None


@router.post("/generate", response_model=ImageResponse)
async def generate_image(request: ImageRequest):
    """
    Generate a Christian-themed image based on the prompt.
    
    The prompt will be checked for safety and transformed into
    a reverent, appropriate image request.
    """
    image_service = get_image_service()
    
    try:
        result = await image_service.generate_image(
            user_request=request.prompt,
            size=request.size,
            quality=request.quality
        )
        
        return ImageResponse(
            success=result.get("success", False),
            image_url=result.get("image_url"),
            error=result.get("error"),
            generated_prompt=result.get("generated_prompt"),
            suggested_alternative=result.get("suggested_alternative")
        )
    except Exception as e:
        return ImageResponse(
            success=False,
            error=str(e)
        )


@router.post("/verse-illustration", response_model=ImageResponse)
async def generate_verse_illustration(request: VerseIllustrationRequest):
    """
    Generate an illustration for a specific Bible verse.
    """
    image_service = get_image_service()
    
    try:
        result = await image_service.generate_verse_illustration(
            verse_reference=request.verse_reference,
            verse_text=request.verse_text
        )
        
        return ImageResponse(
            success=result.get("success", False),
            image_url=result.get("image_url"),
            error=result.get("error"),
            generated_prompt=result.get("generated_prompt")
        )
    except Exception as e:
        return ImageResponse(
            success=False,
            error=str(e)
        )


@router.get("/themes")
async def get_suggested_themes():
    """
    Get suggested Christian image themes.
    """
    image_service = get_image_service()
    themes = image_service.get_suggested_themes()
    
    return {"themes": themes}
