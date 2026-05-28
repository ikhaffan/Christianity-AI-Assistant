"""
Groq API client using OpenAI-compatible API.
Fast LLM inference with free tier available.
"""
import httpx
import json
from typing import Generator, Optional, Dict, Any


class GroqClient:
    """Groq API client using OpenAI-compatible endpoint."""
    
    BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
    
    def __init__(self, api_key: str):
        """
        Initialize Groq client.
        
        Args:
            api_key: Groq API key from console.groq.com
        """
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def send_message(self, model: str, message: str, temperature: float = 0.7) -> Generator[Dict[str, Any], None, None]:
        """
        Send a message to Groq API synchronously.
        
        Args:
            model: Model name (e.g., "llama-3.3-70b-versatile")
            message: The message to send
            temperature: Sampling temperature
            
        Yields:
            Dict with response containing "text" key
        """
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": message}],
            "temperature": temperature,
            "max_tokens": 2048
        }
        
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    self.BASE_URL,
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                text = result["choices"][0]["message"]["content"]
                yield {"text": text}
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise Exception("Invalid Groq API key. Get one free at console.groq.com")
            elif e.response.status_code == 429:
                raise Exception("Groq rate limit exceeded. Please wait a moment and try again.")
            else:
                error_detail = ""
                try:
                    error_detail = e.response.json().get("error", {}).get("message", "")
                except:
                    error_detail = e.response.text
                raise Exception(f"Groq API error: {e.response.status_code} - {error_detail}")
        except Exception as e:
            raise Exception(f"Failed to connect to Groq API: {str(e)}")
    
    def generate(self, model: str, prompt: str, temperature: float = 0.7) -> str:
        """
        Generate a response synchronously.
        
        Args:
            model: Model name
            prompt: The prompt to send
            temperature: Sampling temperature
            
        Returns:
            The response text
        """
        for chunk in self.send_message(model, prompt, temperature):
            return chunk["text"]
        return ""


# Alias for compatibility with existing code
class PoeApi:
    """
    Compatibility wrapper using Groq API.
    Provides same interface as the old PoeApi class.
    """
    
    def __init__(self, api_key: str):
        self.client = GroqClient(api_key)
    
    def send_message(self, model: str, message: str) -> Generator[Dict[str, Any], None, None]:
        """Send message and yield response chunks."""
        return self.client.send_message(model, message)
