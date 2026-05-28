"""
FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import chat, image
from app.config import settings

app = FastAPI(
    title="Christianity AI Assistant",
    description="A grounded, safe AI assistant for Christianity-related questions",
    version="1.0.0"
)

# CORS middleware for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(image.router, prefix="/image", tags=["Image"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Christianity AI Assistant API",
        "docs": "/docs",
        "health": "/health"
    }
