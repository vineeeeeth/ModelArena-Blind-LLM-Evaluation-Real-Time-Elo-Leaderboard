"""Prompt category classifier."""

from __future__ import annotations

import re
import unicodedata

from app.models.tables import BattleCategory


def classify_prompt(text: str) -> BattleCategory:
    """Classify a user prompt into a battle category."""

    # Hindi – detect Devanagari script ratio
    if _devanagari_ratio(text) > 0.3:
        return BattleCategory.hindi

    lower = text.lower()

    # Coding
    code_patterns = [
        r"```",               # code fences
        r"\bdef\s+\w+",       # python function
        r"\bfunction\s+\w+",  # JS function
        r"\bclass\s+\w+",     # class definition
        r"\bimport\s+\w+",    # import statement
        r"\bconst\s+\w+",     # JS const
        r"\breturn\s+",       # return
    ]
    code_keywords = [
        "bug", "code", "program", "compile", "syntax", "debug",
        "algorithm", "implement", "refactor", "api", "endpoint",
        "javascript", "python", "typescript", "java ", "html",
        "css", "sql", "regex", "git", "docker",
    ]
    if any(re.search(p, text) for p in code_patterns):
        return BattleCategory.coding
    if any(kw in lower for kw in code_keywords):
        return BattleCategory.coding

    # Math
    math_symbols = set("∫∑∏√∞±≈≠≤≥÷×∂∇∆")
    if any(c in math_symbols for c in text):
        return BattleCategory.math
    math_keywords = [
        "calculate", "solve", "equation", "integral", "derivative",
        "matrix", "vector", "probability", "theorem", "proof",
        "algebra", "geometry", "trigonometry", "calculus",
        "factorial", "logarithm", "polynomial",
    ]
    if any(kw in lower for kw in math_keywords):
        return BattleCategory.math

    # Summarization
    summarization_keywords = [
        "summarize", "summarise", "tl;dr", "tldr", "summary",
        "summarization", "key points", "main points", "brief overview",
    ]
    if any(kw in lower for kw in summarization_keywords):
        return BattleCategory.summarization
    if len(text) > 1000:
        return BattleCategory.summarization

    return BattleCategory.general


def _devanagari_ratio(text: str) -> float:
    """Return the fraction of characters that are Devanagari."""
    if not text:
        return 0.0
    total = 0
    devanagari = 0
    for ch in text:
        if ch.isspace():
            continue
        total += 1
        try:
            name = unicodedata.name(ch, "")
        except ValueError:
            continue
        if "DEVANAGARI" in name:
            devanagari += 1
    return devanagari / total if total > 0 else 0.0
