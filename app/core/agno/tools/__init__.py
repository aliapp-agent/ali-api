"""Agno tools for enhanced language model capabilities.

This package contains custom tools that can be used with Agno to extend
the capabilities of language models. Currently includes tools for web search
and other external integrations.
"""

from .duckduckgo_search import duckduckgo_search_tool

tools = [duckduckgo_search_tool]
