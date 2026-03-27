"""
TAKTKRONE-I UI Module - Phase 5 Production.

Provides user interfaces including:
- Gradio demo for interactive inference
- Web-based query interface with examples and export
"""

from .demo import create_demo

__all__ = [
    "create_demo",
]
