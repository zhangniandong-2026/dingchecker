#!/usr/bin/env python3
"""Google Gen AI SDK wrapper."""

from __future__ import annotations

from typing import Optional

try:
    from google import genai

    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_AVAILABLE = False


def generate_text(prompt: str, model_name: str, api_key: Optional[str] = None) -> str:
    """Generate text with the unified Google Gen AI SDK."""
    if not GEMINI_AVAILABLE:
        raise RuntimeError("Google Gen AI SDK is not installed")

    client = genai.Client(api_key=api_key) if api_key else genai.Client()
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        return response.text or ""
    finally:
        client.close()
