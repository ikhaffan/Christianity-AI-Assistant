"""
Moderation and safety service for content filtering and adversarial detection.
"""
import re
import json
import asyncio
from typing import Dict, Tuple, Optional
from enum import Enum

from app.services.poe_client import PoeApi

from app.config import settings
from app.prompts.safety import (
    CONTENT_MODERATION_PROMPT,
    IMAGE_SAFETY_PROMPT,
    ADVERSARIAL_PATTERNS,
    REFUSAL_RESPONSES,
    BIBLE_BOOKS
)


class SafetyCategory(Enum):
    SAFE = "SAFE"
    HATEFUL_CONTENT = "HATEFUL_CONTENT"
    MANIPULATION_ATTEMPT = "MANIPULATION_ATTEMPT"
    ADVERSARIAL_PROMPT = "ADVERSARIAL_PROMPT"
    INAPPROPRIATE_REQUEST = "INAPPROPRIATE_REQUEST"
    FAKE_VERSE_CLAIM = "FAKE_VERSE_CLAIM"
    IDEOLOGY_INJECTION = "IDEOLOGY_INJECTION"


class ImageSafetyCategory(Enum):
    SAFE = "SAFE"
    VIOLENT = "VIOLENT"
    OFFENSIVE = "OFFENSIVE"
    INAPPROPRIATE = "INAPPROPRIATE"
    POLICY_VIOLATION = "POLICY_VIOLATION"
    POLITICAL = "POLITICAL"


class ModerationService:
    """Service for content moderation and safety checks."""
    
    def __init__(self):
        self.client = PoeApi(settings.groq_api_key)
        self.model = settings.llm_model
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for fast matching."""
        self.adversarial_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in ADVERSARIAL_PATTERNS
        ]
    
    def _generate_sync(self, prompt: str) -> str:
        """Generate response synchronously using Poe API."""
        try:
            response_text = ""
            for chunk in self.client.send_message(self.model, prompt):
                response_text = chunk["text"]
            return response_text.strip()
        except Exception as e:
            raise Exception(f"Poe API error: {str(e)}")
    
    def _compile_patterns(self):
        """Compile regex patterns for fast matching."""
        self.adversarial_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in ADVERSARIAL_PATTERNS
        ]
    
    def _quick_pattern_check(self, message: str) -> Optional[SafetyCategory]:
        """Fast regex-based check for common adversarial patterns."""
        message_lower = message.lower()
        
        for pattern in self.adversarial_patterns:
            if pattern.search(message_lower):
                # Determine specific category based on pattern
                pattern_str = pattern.pattern
                if "rewrite" in pattern_str or "change" in pattern_str or "alter" in pattern_str:
                    return SafetyCategory.MANIPULATION_ATTEMPT
                elif "ignore" in pattern_str or "forget" in pattern_str or "bypass" in pattern_str:
                    return SafetyCategory.ADVERSARIAL_PROMPT
                else:
                    return SafetyCategory.ADVERSARIAL_PROMPT
        
        return None
    
    def _check_fake_verse(self, message: str) -> Tuple[bool, Optional[str]]:
        """Check if message references a potentially fake Bible verse."""
        # Pattern to match verse references like "John 25:1" or "Genesis 100:5"
        verse_pattern = r'\b([1-3]?\s*[A-Za-z]+)\s+(\d+):(\d+)\b'
        
        matches = re.findall(verse_pattern, message)
        
        for match in matches:
            book_name = match[0].strip().lower()
            chapter = int(match[1])
            
            # Normalize book name
            book_name = re.sub(r'^(\d)\s*', r'\1 ', book_name)
            
            # Check if book exists
            if book_name in BIBLE_BOOKS:
                max_chapters = BIBLE_BOOKS[book_name]
                if chapter > max_chapters:
                    return True, f"{match[0]} {match[1]}:{match[2]}"
        
        return False, None
    
    async def check_message_safety(self, message: str) -> Dict:
        """
        Check if a user message is safe to process.
        
        Returns:
            Dict with keys: is_safe, category, confidence, reasoning, refusal_message
        """
        # Quick pattern check first
        quick_result = self._quick_pattern_check(message)
        if quick_result:
            return {
                "is_safe": False,
                "category": quick_result.value,
                "confidence": 0.95,
                "reasoning": "Detected adversarial pattern in message",
                "refusal_message": REFUSAL_RESPONSES.get(
                    quick_result.value, 
                    "I'm not able to help with that request."
                )
            }
        
        # Check for fake verse claims
        is_fake, fake_ref = self._check_fake_verse(message)
        if is_fake:
            # Don't immediately refuse - let the system handle gracefully
            return {
                "is_safe": True,
                "category": SafetyCategory.SAFE.value,
                "confidence": 1.0,
                "reasoning": f"Potentially invalid verse reference: {fake_ref}",
                "flag": "POTENTIAL_FAKE_VERSE",
                "flagged_reference": fake_ref
            }
        
        # LLM-based moderation for nuanced cases
        try:
            prompt = f"""You are a content moderation system. Analyze messages for safety concerns. Respond only with valid JSON.

{CONTENT_MODERATION_PROMPT.format(message=message)}"""
            
            result_text = await asyncio.to_thread(self._generate_sync, prompt)
            
            # Parse JSON response
            # Handle potential markdown code blocks
            if "```" in result_text:
                result_text = re.search(r'```(?:json)?\s*(.*?)\s*```', result_text, re.DOTALL)
                if result_text:
                    result_text = result_text.group(1)
            
            result = json.loads(result_text)
            
            category = result.get("category", "SAFE")
            is_safe = category == "SAFE"
            
            return {
                "is_safe": is_safe,
                "category": category,
                "confidence": result.get("confidence", 0.5),
                "reasoning": result.get("reasoning", ""),
                "refusal_message": REFUSAL_RESPONSES.get(category) if not is_safe else None
            }
            
        except Exception as e:
            # Default to safe if moderation fails (fail-open for usability)
            print(f"Moderation error: {e}")
            return {
                "is_safe": True,
                "category": SafetyCategory.SAFE.value,
                "confidence": 0.5,
                "reasoning": "Moderation check failed, proceeding with caution"
            }
    
    async def check_image_safety(self, request: str) -> Dict:
        """
        Check if an image generation request is safe.
        
        Returns:
            Dict with keys: is_safe, category, confidence, reasoning, safe_alternative
        """
        try:
            prompt = f"""You are an image content safety system for a Christian AI assistant. Analyze image requests. Respond only with valid JSON.

{IMAGE_SAFETY_PROMPT.format(request=request)}"""
            
            result_text = await asyncio.to_thread(self._generate_sync, prompt)
            
            # Handle potential markdown code blocks
            if "```" in result_text:
                result_text = re.search(r'```(?:json)?\s*(.*?)\s*```', result_text, re.DOTALL)
                if result_text:
                    result_text = result_text.group(1)
            
            result = json.loads(result_text)
            
            category = result.get("category", "SAFE")
            is_safe = category == "SAFE"
            
            return {
                "is_safe": is_safe,
                "category": category,
                "confidence": result.get("confidence", 0.5),
                "reasoning": result.get("reasoning", ""),
                "safe_alternative": result.get("safe_alternative"),
                "refusal_message": REFUSAL_RESPONSES.get(category) if not is_safe else None
            }
            
        except Exception as e:
            print(f"Image safety check error: {e}")
            # Default to requiring review
            return {
                "is_safe": False,
                "category": "POLICY_VIOLATION",
                "confidence": 0.5,
                "reasoning": "Safety check failed, request requires review",
                "refusal_message": "I couldn't verify the safety of this image request. Please try a different description."
            }
    
    def validate_response_grounding(self, response: str, context: str) -> Dict:
        """
        Validate that a response is properly grounded in the provided context.
        
        This checks that any Bible verses cited in the response actually exist
        in the context provided.
        """
        # Extract verse references from response
        verse_pattern = r'\[?([1-3]?\s*[A-Za-z]+\s+\d+:\d+)\]?'
        cited_refs = re.findall(verse_pattern, response)
        
        issues = []
        for ref in cited_refs:
            if ref.lower() not in context.lower():
                issues.append(f"Verse '{ref}' not found in provided context")
        
        return {
            "is_grounded": len(issues) == 0,
            "issues": issues,
            "cited_references": cited_refs
        }


# Singleton instance
_moderation_service: Optional[ModerationService] = None


def get_moderation_service() -> ModerationService:
    """Get or create moderation service singleton."""
    global _moderation_service
    if _moderation_service is None:
        _moderation_service = ModerationService()
    return _moderation_service
