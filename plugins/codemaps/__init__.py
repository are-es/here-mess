"""Code-Maps Plugin Interface & Auto-Prompt Injection."""

from __future__ import annotations

from plugins.codemaps.tools import handle_codemaps, resolve_codemaps_dir


def system_prompt_block() -> str:
    """Cold-start prompt injection for AI Agents."""
    return (
        "# Code-Maps Architecture Protocol\n"
        "This project supports pre-computed code architecture maps. "
        "Before scanning or reading files individually, use the `code_maps` tool (action='scan' or action='query') "
        "to check for an existing AST graph and project memory.\n"
    )
