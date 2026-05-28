"""
Chat API routes.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

from app.services.llm_service import get_llm_service
from app.services.memory import get_memory_service

router = APIRouter()


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str
    session_id: str
    citations: List[dict] = []
    is_safe: bool = True
    is_grounded: bool = True


class VerseRequest(BaseModel):
    """Request model for verse lookup."""
    reference: str = Field(..., min_length=1, max_length=100)
    session_id: Optional[str] = None


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message and get a grounded response.
    
    The response will include Bible verse citations when relevant.
    """
    llm_service = get_llm_service()
    memory_service = get_memory_service()
    
    # Get or create session
    session_id = memory_service.get_or_create_session(request.session_id)
    
    try:
        result = await llm_service.generate_response(
            user_message=request.message,
            session_id=session_id
        )
        
        return ChatResponse(
            response=result["response"],
            session_id=session_id,
            citations=result.get("citations", []),
            is_safe=result.get("is_safe", True),
            is_grounded=result.get("is_grounded", True)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verse")
async def lookup_verse(request: VerseRequest):
    """
    Look up a specific Bible verse by reference.
    """
    llm_service = get_llm_service()
    memory_service = get_memory_service()
    
    session_id = memory_service.get_or_create_session(request.session_id)
    
    try:
        result = await llm_service.handle_verse_query(
            reference=request.reference,
            session_id=session_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}")
async def get_history(session_id: str):
    """
    Get conversation history for a session.
    """
    memory_service = get_memory_service()
    
    history = memory_service.get_history(session_id)
    metadata = memory_service.get_session_metadata(session_id)
    
    if not metadata:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "metadata": metadata,
        "messages": history
    }


@router.delete("/history/{session_id}")
async def clear_history(session_id: str):
    """
    Clear conversation history for a session.
    """
    memory_service = get_memory_service()
    memory_service.clear_session(session_id)
    
    return {"message": "Session cleared", "session_id": session_id}


@router.post("/session")
async def create_session():
    """
    Create a new conversation session.
    """
    memory_service = get_memory_service()
    session_id = memory_service.create_session()
    
    return {"session_id": session_id}
