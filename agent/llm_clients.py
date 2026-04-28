"""Shared LLM client helpers.

Centralizes OpenAI and Anthropic client instantiation so that all agent
modules and baselines pull from a single configured place. Loads .env on
import.
"""
from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


# Default model choices. Can be overridden per-call.
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_OPENAI_FRONTIER = "gpt-4o"
DEFAULT_ANTHROPIC_MODEL = "claude-3-5-sonnet-latest"


@lru_cache(maxsize=1)
def openai_client():
    from openai import OpenAI

    return OpenAI(api_key=os.environ["OPENAI_API_KEY"])


@lru_cache(maxsize=1)
def anthropic_client():
    from anthropic import Anthropic

    return Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


@lru_cache(maxsize=1)
def tavily_client():
    from tavily import TavilyClient

    return TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
