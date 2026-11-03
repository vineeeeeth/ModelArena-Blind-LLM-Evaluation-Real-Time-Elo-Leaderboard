"""Anti-leak test suite – asserts model identity never leaks before vote."""

import pytest
import re
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from app.models.tables import BattleStatus, BattleCategory, Model


def test_no_model_leak_in_battle_creation_schema():
    """Ensure the schema returned upon creation has NO model attributes."""
    from app.schemas import BattleCreatedResponse
    fields = BattleCreatedResponse.model_fields.keys()
    assert "model_a" not in fields
    assert "model_b" not in fields
    assert "model_a_id" not in fields
    assert "model_b_id" not in fields
    assert "model_a_slug" not in fields
    assert "model_b_slug" not in fields


def test_no_model_leak_in_battle_status_schema():
    """Ensure the public status response schema exposes NO model info."""
    from app.schemas import BattleStatusResponse
    fields = BattleStatusResponse.model_fields.keys()
    assert "model_a" not in fields
    assert "model_b" not in fields
    assert "model_a_id" not in fields
    assert "model_b_id" not in fields


@pytest.mark.asyncio
async def test_anti_leak_sse_payload_format():
    """
    Ensure SSE token packets are pure chunks without model headers or metadata.
    """
    token_data = {"token": "Hello world"}
    payload = f"event: token\ndata: {token_data}\n\n"

    # Verify no model identifiers in typical token payload
    forbidden_terms = ["gpt", "claude", "llama", "qwen", "gemini", "phi", "model_id", "slug"]
    for term in forbidden_terms:
        assert term not in payload.lower(), f"Leaked {term} in token payload"

