"""
Conversation memory service for maintaining chat history.
"""
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
import uuid


@dataclass
class Message:
    """Represents a single message in a conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)


@dataclass
class Conversation:
    """Represents a conversation session."""
    session_id: str
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    user_denomination: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


class MemoryService:
    """Service for managing conversation memory."""
    
    def __init__(self, max_history: int = 20):
        self.conversations: Dict[str, Conversation] = {}
        self.max_history = max_history
    
    def create_session(self) -> str:
        """Create a new conversation session."""
        session_id = str(uuid.uuid4())
        self.conversations[session_id] = Conversation(session_id=session_id)
        return session_id
    
    def get_or_create_session(self, session_id: Optional[str] = None) -> str:
        """Get existing session or create new one."""
        if session_id and session_id in self.conversations:
            return session_id
        return self.create_session()
    
    def add_message(
        self, 
        session_id: str, 
        role: str, 
        content: str,
        metadata: Optional[Dict] = None
    ):
        """Add a message to the conversation."""
        if session_id not in self.conversations:
            self.conversations[session_id] = Conversation(session_id=session_id)
        
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        
        self.conversations[session_id].messages.append(message)
        
        # Trim history if needed
        if len(self.conversations[session_id].messages) > self.max_history:
            # Keep the most recent messages
            self.conversations[session_id].messages = \
                self.conversations[session_id].messages[-self.max_history:]
    
    def get_history(
        self, 
        session_id: str, 
        max_messages: Optional[int] = None
    ) -> List[Dict]:
        """Get conversation history for a session."""
        if session_id not in self.conversations:
            return []
        
        messages = self.conversations[session_id].messages
        
        if max_messages:
            messages = messages[-max_messages:]
        
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in messages
        ]
    
    def get_history_for_llm(self, session_id: str) -> List[Dict]:
        """Get conversation history formatted for LLM context."""
        if session_id not in self.conversations:
            return []
        
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.conversations[session_id].messages
        ]
    
    def format_history_string(self, session_id: str) -> str:
        """Format conversation history as a string for prompt injection."""
        history = self.get_history(session_id)
        
        if not history:
            return "No previous conversation."
        
        formatted = []
        for msg in history[-10:]:  # Last 10 messages
            role = "User" if msg["role"] == "user" else "Assistant"
            formatted.append(f"{role}: {msg['content']}")
        
        return "\n".join(formatted)
    
    def set_denomination(self, session_id: str, denomination: str):
        """Set the user's denomination preference for a session."""
        if session_id in self.conversations:
            self.conversations[session_id].user_denomination = denomination
    
    def get_denomination(self, session_id: str) -> Optional[str]:
        """Get the user's denomination preference for a session."""
        if session_id in self.conversations:
            return self.conversations[session_id].user_denomination
        return None
    
    def clear_session(self, session_id: str):
        """Clear a conversation session."""
        if session_id in self.conversations:
            del self.conversations[session_id]
    
    def get_session_metadata(self, session_id: str) -> Optional[Dict]:
        """Get session metadata."""
        if session_id not in self.conversations:
            return None
        
        conv = self.conversations[session_id]
        return {
            "session_id": conv.session_id,
            "created_at": conv.created_at.isoformat(),
            "message_count": len(conv.messages),
            "user_denomination": conv.user_denomination
        }


# Singleton instance
_memory_service: Optional[MemoryService] = None


def get_memory_service() -> MemoryService:
    """Get or create memory service singleton."""
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service
