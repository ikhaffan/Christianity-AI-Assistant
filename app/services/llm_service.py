"""
LLM orchestration service for generating responses using Poe API.
"""
from typing import Dict, List, Optional
import re
import asyncio

from app.services.poe_client import PoeApi

from app.config import settings
from app.prompts.system import (
    MAIN_SYSTEM_PROMPT,
    DENOMINATION_DETECTION_PROMPT,
    QUERY_ENHANCEMENT_PROMPT
)
from app.services.rag_service import get_rag_service
from app.services.memory import get_memory_service
from app.services.moderation import get_moderation_service


class LLMService:
    """Service for LLM-based response generation with grounding."""
    
    def __init__(self):
        self.client = PoeApi(settings.groq_api_key)
        self.model = settings.llm_model
        self.rag_service = get_rag_service()
        self.memory_service = get_memory_service()
        self.moderation_service = get_moderation_service()
    
    def _generate_sync(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate response synchronously using Poe API."""
        try:
            response_text = ""
            for chunk in self.client.send_message(self.model, prompt):
                response_text = chunk["text"]
            return response_text.strip()
        except Exception as e:
            raise Exception(f"Poe API error: {str(e)}")
    
    async def enhance_query(self, query: str) -> str:
        """Enhance user query for better Bible verse retrieval."""
        try:
            prompt = f"""You are a query enhancement system. Transform questions into search queries optimized for Bible verse retrieval. Output only the enhanced query.

{QUERY_ENHANCEMENT_PROMPT.format(question=query)}"""
            
            response = await asyncio.to_thread(self._generate_sync, prompt, 0.3, 100)
            return response
        except Exception:
            return query  # Fall back to original query
    
    async def detect_denomination(self, message: str) -> Optional[str]:
        """Detect if user indicates a specific denomination."""
        try:
            prompt = DENOMINATION_DETECTION_PROMPT.format(message=message)
            response = await asyncio.to_thread(self._generate_sync, prompt, 0, 50)
            result = response.strip()
            if result != "UNKNOWN":
                return result
            return None
        except Exception:
            return None
    
    async def generate_response(
        self,
        user_message: str,
        session_id: str,
        include_citations: bool = True
    ) -> Dict:
        """
        Generate a grounded response to a user message.
        
        Args:
            user_message: The user's question or message
            session_id: Conversation session ID
            include_citations: Whether to include Bible verse citations
            
        Returns:
            Dict with response, citations, and metadata
        """
        # Step 1: Check message safety
        safety_check = await self.moderation_service.check_message_safety(user_message)
        
        if not safety_check["is_safe"]:
            # Return refusal for unsafe content
            return {
                "response": safety_check["refusal_message"],
                "citations": [],
                "is_safe": False,
                "safety_category": safety_check["category"]
            }
        
        # Step 2: Check for denomination indication and store
        denomination = await self.detect_denomination(user_message)
        if denomination:
            self.memory_service.set_denomination(session_id, denomination)
        
        # Step 3: Enhance query for better retrieval
        enhanced_query = await self.enhance_query(user_message)
        
        # Step 4: Retrieve relevant Bible verses
        retrieved_verses = self.rag_service.retrieve_verses(
            enhanced_query,
            top_k=settings.retrieval_top_k
        )
        
        # Format context from retrieved verses
        context = self.rag_service.format_context(retrieved_verses)
        
        # Step 5: Get conversation history
        history = self.memory_service.format_history_string(session_id)
        
        # Step 6: Build system prompt with context
        system_prompt = MAIN_SYSTEM_PROMPT.format(
            context=context,
            history=history
        )
        
        # Add denomination context if known
        user_denomination = self.memory_service.get_denomination(session_id)
        if user_denomination:
            system_prompt += f"\n\nNote: The user has indicated they are {user_denomination}. Be mindful of their tradition while remaining accurate and balanced."
        
        # Step 7: Generate response with Poe API
        full_prompt = f"{system_prompt}\n\nUser: {user_message}"
        
        assistant_response = await asyncio.to_thread(self._generate_sync, full_prompt, 0.7, 1000)
        
        # Step 8: Validate response grounding
        grounding_check = self.moderation_service.validate_response_grounding(
            assistant_response, 
            context
        )
        
        # Step 9: Store messages in memory
        self.memory_service.add_message(session_id, "user", user_message)
        self.memory_service.add_message(
            session_id, 
            "assistant", 
            assistant_response,
            metadata={"grounding_check": grounding_check}
        )
        
        # Step 10: Extract citations from response
        citations = self._extract_citations(assistant_response, retrieved_verses)
        
        return {
            "response": assistant_response,
            "citations": citations,
            "retrieved_verses": [
                {"reference": v["reference"], "text": v["text"]}
                for v in retrieved_verses
            ],
            "is_safe": True,
            "is_grounded": grounding_check["is_grounded"],
            "grounding_issues": grounding_check.get("issues", []),
            "session_id": session_id
        }
    
    def _extract_citations(
        self, 
        response: str, 
        available_verses: List[Dict]
    ) -> List[Dict]:
        """Extract Bible citations from the response."""
        citations = []
        
        # Pattern to match verse references
        verse_pattern = r'\[?([1-3]?\s*[A-Za-z]+\s+\d+:\d+(?:-\d+)?)\]?'
        matches = re.findall(verse_pattern, response)
        
        for match in matches:
            # Try to find the verse in our retrieved verses
            for verse in available_verses:
                if verse["reference"].lower() in match.lower():
                    citations.append({
                        "reference": verse["reference"],
                        "text": verse["text"]
                    })
                    break
        
        return citations
    
    async def handle_verse_query(
        self,
        reference: str,
        session_id: str
    ) -> Dict:
        """
        Handle a direct query for a specific Bible verse.
        
        Args:
            reference: Bible verse reference (e.g., "John 3:16")
            session_id: Conversation session ID
            
        Returns:
            Dict with verse text or error message
        """
        # Validate the reference exists
        is_valid, verse_data = self.rag_service.validate_verse_reference(reference)
        
        if is_valid and verse_data:
            response = f"**{verse_data['reference']}**\n\n\"{verse_data['text']}\""
            
            self.memory_service.add_message(session_id, "user", f"What does {reference} say?")
            self.memory_service.add_message(session_id, "assistant", response)
            
            return {
                "response": response,
                "verse": verse_data,
                "is_valid": True
            }
        else:
            # Verse not found - provide helpful response
            response = f"I couldn't find {reference} in my Bible reference database. This could mean:\n\n"
            response += "1. The verse reference might not exist (please check book, chapter, and verse numbers)\n"
            response += "2. It might be a less common passage not in my current database\n\n"
            response += "Would you like me to help you find a verse on a similar topic instead?"
            
            self.memory_service.add_message(session_id, "user", f"What does {reference} say?")
            self.memory_service.add_message(session_id, "assistant", response)
            
            return {
                "response": response,
                "is_valid": False,
                "queried_reference": reference
            }


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create LLM service singleton."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
