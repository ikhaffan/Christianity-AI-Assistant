"""
Streamlit Chat Interface for Christianity AI Assistant
"""
import streamlit as st
import requests
import uuid
from typing import Optional
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

# Import services directly for Streamlit (avoiding FastAPI)
from app.services.llm_service import get_llm_service
from app.services.image_gen import get_image_service
from app.services.memory import get_memory_service
from app.services.rag_service import get_rag_service
import asyncio

# Page configuration
st.set_page_config(
    page_title="Christianity AI Assistant",
    page_icon="✝️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2c3e50;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #7f8c8d;
        text-align: center;
        margin-bottom: 2rem;
    }
    .verse-citation {
        background-color: #1e2a3a;
        border-left: 4px solid #3498db;
        padding: 1rem;
        margin: 0.5rem 0;
        font-style: italic;
        color: #e0e0e0;
        border-radius: 4px;
    }
    .verse-citation strong {
        color: #64b5f6;
    }
    .safety-warning {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .stChatMessage {
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "services_initialized" not in st.session_state:
        st.session_state.services_initialized = False


def initialize_services():
    """Initialize all services."""
    if not st.session_state.services_initialized:
        try:
            # Initialize RAG service and index Bible verses if needed
            rag_service = get_rag_service()
            if rag_service.get_verse_count() == 0:
                with st.spinner("Initializing Bible database... This may take a minute on first run."):
                    rag_service.index_bible_verses()
            st.session_state.services_initialized = True
            return True
        except Exception as e:
            st.error(f"Failed to initialize services: {str(e)}")
            st.info("Please check that your OpenAI API key is set in the .env file.")
            return False
    return True


def run_async(coro):
    """Run async function in Streamlit."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def display_sidebar():
    """Display sidebar with options and information."""
    with st.sidebar:
        st.markdown("### ✝️ Christianity AI Assistant")
        st.markdown("---")
        
        # Info section
        st.markdown("#### About")
        st.markdown("""
        This AI assistant helps with:
        - Biblical questions & discussions
        - Scripture references with citations
        - Christian-themed image generation
        - Theological conversations
        """)
        
        st.markdown("---")
        
        # Features
        st.markdown("#### Features")
        st.markdown("""
        ✓ RAG-based Bible grounding  
        ✓ Verse validation & citations  
        ✓ Denomination awareness  
        ✓ Content safety filters  
        ✓ Image generation  
        """)
        
        st.markdown("---")
        
        # Image generation section
        st.markdown("#### 🎨 Generate Christian Image")
        image_prompt = st.text_area(
            "Describe the image you'd like:",
            placeholder="E.g., A peaceful sunrise over a church in the countryside",
            height=100
        )
        
        if st.button("Generate Image", type="secondary"):
            if image_prompt:
                generate_image(image_prompt)
            else:
                st.warning("Please enter an image description.")
        
        # Suggested themes
        with st.expander("💡 Suggested Themes"):
            themes = [
                "A peaceful scene of prayer",
                "God's creation in nature",
                "Light breaking through clouds",
                "A shepherd with sheep (Psalm 23)",
                "An open Bible with candle light",
                "A dove representing peace",
                "Seeds growing into plants"
            ]
            for theme in themes:
                if st.button(theme, key=f"theme_{theme[:20]}"):
                    generate_image(theme)
        
        st.markdown("---")
        
        # Session controls
        st.markdown("#### Session")
        if st.button("🔄 New Conversation"):
            st.session_state.messages = []
            st.session_state.session_id = str(uuid.uuid4())
            memory_service = get_memory_service()
            memory_service.clear_session(st.session_state.session_id)
            st.rerun()
        
        # Database info
        try:
            rag_service = get_rag_service()
            verse_count = rag_service.get_verse_count()
            st.caption(f"📖 {verse_count} Bible verses indexed")
        except:
            pass


def generate_image(prompt: str):
    """Generate a Christian-themed image."""
    with st.spinner("Creating your image..."):
        try:
            image_service = get_image_service()
            result = run_async(image_service.generate_image(prompt))
            
            if result.get("success"):
                # Check if we have an actual image or just a prompt
                if result.get("image_path"):
                    st.image(result["image_path"], caption=prompt)
                    st.success("Image generated successfully!")
                elif result.get("image_url"):
                    st.image(result["image_url"], caption=prompt)
                    st.success("Image generated successfully!")
                elif result.get("prompt_ready"):
                    # No image API available, show the generated prompt
                    st.info("🎨 Image prompt generated! Copy this to use with an image generator:")
                    st.code(result.get("generated_prompt", prompt), language=None)
                    st.caption("Use this prompt with Midjourney, DALL-E, Stable Diffusion, or similar services.")
                else:
                    st.warning("Image generation is not configured. Here's your enhanced prompt:")
                    st.code(result.get("generated_prompt", prompt), language=None)
            else:
                st.error(result.get("error", "Failed to generate image"))
                if result.get("suggested_alternative"):
                    st.info(f"💡 Try instead: {result['suggested_alternative']}")
        except Exception as e:
            st.error(f"Error generating image: {str(e)}")


def display_chat_history():
    """Display chat message history."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Display citations if available
            if message.get("citations"):
                with st.expander("📖 Scripture Citations"):
                    for citation in message["citations"]:
                        st.markdown(f"""
                        <div class="verse-citation">
                            <strong>{citation['reference']}</strong><br>
                            "{citation['text']}"
                        </div>
                        """, unsafe_allow_html=True)


def process_user_message(user_input: str):
    """Process user message and get response."""
    # Add user message to history
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                llm_service = get_llm_service()
                result = run_async(llm_service.generate_response(
                    user_message=user_input,
                    session_id=st.session_state.session_id
                ))
                
                response = result["response"]
                citations = result.get("citations", [])
                
                # Display response
                st.markdown(response)
                
                # Display citations if available
                if citations:
                    with st.expander("📖 Scripture Citations"):
                        for citation in citations:
                            st.markdown(f"""
                            <div class="verse-citation">
                                <strong>{citation['reference']}</strong><br>
                                "{citation['text']}"
                            </div>
                            """, unsafe_allow_html=True)
                
                # Show grounding status
                if not result.get("is_grounded", True):
                    st.warning("⚠️ Some references in this response may not be fully verified.")
                
                # Add to message history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "citations": citations
                })
                
            except Exception as e:
                error_msg = f"I apologize, but I encountered an error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })


def main():
    """Main application entry point."""
    init_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">✝️ Christianity AI Assistant</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Ask questions about the Bible, Christian faith, and receive scripture-grounded answers</p>', unsafe_allow_html=True)
    
    # Initialize services
    if not initialize_services():
        st.stop()
    
    # Display sidebar
    display_sidebar()
    
    # Main chat area
    st.markdown("---")
    
    # Display chat history
    display_chat_history()
    
    # Chat input
    if user_input := st.chat_input("Ask a question about Christianity or the Bible..."):
        process_user_message(user_input)
    
    # Example questions (only show if no messages)
    if not st.session_state.messages:
        st.markdown("### 💡 Example Questions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            example_questions = [
                "What does the Bible say about love?",
                "How can I find peace during difficult times?",
                "What is the meaning of John 3:16?",
                "What are the fruits of the Spirit?"
            ]
            for q in example_questions:
                if st.button(q, key=f"q1_{q[:20]}"):
                    process_user_message(q)
                    st.rerun()
        
        with col2:
            example_questions = [
                "How do I pray effectively?",
                "What does Psalm 23 teach us?",
                "How do Catholics and Protestants differ?",
                "What is grace according to the Bible?"
            ]
            for q in example_questions:
                if st.button(q, key=f"q2_{q[:20]}"):
                    process_user_message(q)
                    st.rerun()


if __name__ == "__main__":
    main()
