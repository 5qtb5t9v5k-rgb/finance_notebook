"""LLM client for OpenAI API integration."""

from typing import List, Dict, Optional
import os


def get_llm_response(
    messages: List[Dict[str, str]], 
    api_key: str, 
    model: str = "gpt-4o-mini"
) -> str:
    """
    Get response from OpenAI API.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content' keys
        api_key: OpenAI API key
        model: Model to use (default: gpt-3.5-turbo)
        
    Returns:
        Response text from the model
        
    Raises:
        ImportError: If openai package is not installed
        Exception: For API errors, timeouts, etc.
    """
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError(
            "OpenAI package is not installed. Install it with: pip install openai"
        )
    
    if not api_key:
        raise ValueError("API key is required")
    
    if not messages:
        raise ValueError("Messages list cannot be empty")
    
    try:
        client = OpenAI(api_key=api_key)
        
        # O1-mallit eivät tue temperature-parametria
        if model.startswith("o1"):
            # O1-mallit käyttävät oletusarvoisia parametreja
            response = client.chat.completions.create(
                model=model,
                messages=messages
            )
        elif "gpt-5" in model.lower() or model.startswith("gpt-5"):
            # GPT-5-mallit käyttävät max_completion_tokens eikä max_tokens
            # GPT-5-mallit eivät tue temperature-parametria, käytetään ilman sitä
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_completion_tokens=1000
            )
        else:
            # Muut mallit (gpt-4o-mini, jne.) käyttävät temperaturea ja max_tokens
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
        
        # Check if response is valid
        if not response or not response.choices or len(response.choices) == 0:
            raise Exception("API returned empty response")
        
        content = response.choices[0].message.content
        if content is None:
            raise Exception("API returned None content")
        
        return content.strip()
        
    except Exception as e:
        # Re-raise with more context
        error_msg = str(e)
        if "rate limit" in error_msg.lower():
            raise Exception("API rate limit exceeded. Please try again later.")
        elif "timeout" in error_msg.lower():
            raise Exception("Request timed out. Please try again.")
        elif "invalid" in error_msg.lower() and "api key" in error_msg.lower():
            raise Exception("Invalid API key. Please check your OPENAI_API_KEY environment variable.")
        else:
            raise Exception(f"OpenAI API error: {error_msg}")

