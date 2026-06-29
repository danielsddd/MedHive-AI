"""
LLM gateway tests. Confirm offline mode returns a usable stub completion with no network,
that the gateway status reports offline without keys, and (with a mocked litellm) that a
primary RateLimitError correctly triggers the configured fallback model — the resilience
behaviour the CI quota-protection rule depends on.
"""
import sys
import types

import pytest

from services import llm_gateway


@pytest.mark.asyncio
async def test_offline_returns_stub():
    out = await llm_gateway.complete([{"role": "user", "content": "hello"}])
    assert "stub" in out


def test_gateway_status_offline():
    assert llm_gateway.gateway_status() == "offline"


@pytest.mark.asyncio
async def test_fallback_fires_on_rate_limit(monkeypatch):
    calls = []

    class RateLimitError(Exception):
        pass

    async def fake_acompletion(model, messages, max_tokens, **kwargs):
        calls.append(model)
        if len(calls) == 1:
            raise RateLimitError("429")

        class M:
            class choices:
                pass

        msg = types.SimpleNamespace(content="fallback-ok")
        choice = types.SimpleNamespace(message=msg)
        return types.SimpleNamespace(choices=[choice])

    fake_litellm = types.SimpleNamespace(
        acompletion=fake_acompletion,
        exceptions=types.SimpleNamespace(RateLimitError=RateLimitError),
    )
    monkeypatch.setitem(sys.modules, "litellm", fake_litellm)
    monkeypatch.setattr(llm_gateway.settings, "LLM_MODE", "live")

    out = await llm_gateway.complete(
        [{"role": "user", "content": "x"}], model="primary/model", fallback="fallback/model"
    )
    assert out == "fallback-ok"
    assert calls == ["primary/model", "fallback/model"]
