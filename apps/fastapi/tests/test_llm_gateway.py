"""
LLM gateway tests. The gateway is live-only — no offline stub mode. These tests mock
litellm directly (monkeypatch sys.modules) so no real network call or real API key is
ever needed. Covers: gateway_status() reflects whether keys are configured, and a
RateLimitError on the first configured key correctly rotates to the next key (Daniel ->
Roei) before giving up — the resilience behaviour the dual-key quota-protection design
depends on.

Patching note: settings is a Pydantic BaseSettings instance, so monkeypatch.setattr on
the *instance* rejects gemini_keys (it's a method, not a declared field). Instead we
patch the *class* method via type(settings), which Pydantic permits and which affects
the same singleton instance the gateway uses.
"""
import sys
import types

import pytest

from services import llm_gateway


def test_gateway_status_live_with_keys():
    # CI injects placeholder Gemini/Groq keys via env, so settings.llm_is_live() is True.
    assert llm_gateway.gateway_status() == "live"


@pytest.mark.asyncio
async def test_rotates_to_second_key_on_rate_limit(monkeypatch):
    calls = []

    class RateLimitError(Exception):
        pass

    async def fake_acompletion(model, messages, max_tokens, api_key, **kwargs):
        calls.append(api_key)
        if len(calls) == 1:
            raise RateLimitError("429")
        msg = types.SimpleNamespace(content="rotated-ok")
        choice = types.SimpleNamespace(message=msg)
        return types.SimpleNamespace(choices=[choice])

    fake_litellm = types.SimpleNamespace(
        acompletion=fake_acompletion,
        exceptions=types.SimpleNamespace(RateLimitError=RateLimitError),
    )
    monkeypatch.setitem(sys.modules, "litellm", fake_litellm)
    monkeypatch.setattr(
        type(llm_gateway.settings), "gemini_keys", lambda self: ["daniel-key", "roei-key"]
    )

    out = await llm_gateway.complete([{"role": "user", "content": "x"}], model="test/model")
    assert out == "rotated-ok"
    assert calls == ["daniel-key", "roei-key"]


@pytest.mark.asyncio
async def test_raises_rate_limit_error_when_all_keys_exhausted(monkeypatch):
    class RateLimitError(Exception):
        pass

    async def always_rate_limited(model, messages, max_tokens, api_key, **kwargs):
        raise RateLimitError("429")

    fake_litellm = types.SimpleNamespace(
        acompletion=always_rate_limited,
        exceptions=types.SimpleNamespace(RateLimitError=RateLimitError),
    )
    monkeypatch.setitem(sys.modules, "litellm", fake_litellm)
    monkeypatch.setattr(type(llm_gateway.settings), "gemini_keys", lambda self: ["only-key"])

    from core.errors import APIError

    with pytest.raises(APIError) as exc_info:
        await llm_gateway.complete([{"role": "user", "content": "x"}], model="test/model")
    assert exc_info.value.code == "rate_limit_exceeded"
    assert exc_info.value.status_code == 429