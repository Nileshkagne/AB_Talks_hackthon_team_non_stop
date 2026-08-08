"""
Tests for LLM Model Fallback Chain & Error Classification.
"""

from unittest.mock import MagicMock, patch
import pytest

from app.llm import gemini
from app.llm.config import MODEL_FALLBACK_CHAIN
from app.llm.gemini import GeminiError, is_daily_quota_error, is_per_minute_rate_limit_error


def test_error_classification():
    """Verify daily vs per-minute quota error classification."""
    # Daily quota error (RPD)
    daily_err = Exception("429 RESOURCE_EXHAUSTED. Quota exceeded for metric: generate_content_free_tier_requests, limit: 20, model: gemini-3.6-flash. PerDay limit hit.")
    assert is_daily_quota_error(daily_err) is True
    assert is_per_minute_rate_limit_error(daily_err) is False

    # Per-minute rate limit error (RPM)
    minute_err = Exception("429 RESOURCE_EXHAUSTED. Rate limit exceeded: 15 PerMinute (RPM). Please retry in 2s.")
    assert is_daily_quota_error(minute_err) is False
    assert is_per_minute_rate_limit_error(minute_err) is True

    # Non-429 error
    other_err = Exception("500 Internal Server Error")
    assert is_daily_quota_error(other_err) is False
    assert is_per_minute_rate_limit_error(other_err) is False


@patch("app.llm.gemini._get_client")
@patch("app.llm.gemini._wait_for_rate_limit")
def test_model_fallback_chain_daily_quota(mock_wait, mock_get_client):
    """
    Test 1: Daily quota exhaustion on model 1 and model 2 immediately falls through to model 3.
    Model 3 succeeds and returns _model_used reflecting model 3.
    """
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    daily_quota_exc = Exception(
        "429 RESOURCE_EXHAUSTED. Quota exceeded: GenerateRequestsPerDayPerProjectPerModel-FreeTier"
    )

    def side_effect(model, contents, config):
        if model == MODEL_FALLBACK_CHAIN[0]:
            raise daily_quota_exc
        elif model == MODEL_FALLBACK_CHAIN[1]:
            raise daily_quota_exc
        elif model == MODEL_FALLBACK_CHAIN[2]:
            resp = MagicMock()
            resp.text = '{"question": "What is attention in Transformer architectures?", "type": "conceptual"}'
            return resp
        raise Exception(f"Unexpected model call: {model}")

    mock_client.models.generate_content.side_effect = side_effect

    res = gemini.generate_structured(
        prompt="Test prompt",
        system_instruction="Test system",
    )

    assert res["question"] == "What is attention in Transformer architectures?"
    assert res["_model_used"] == MODEL_FALLBACK_CHAIN[2]

    # Verify model 1 and model 2 were called exactly once (skipped immediately, 0 retries)
    calls = mock_client.models.generate_content.call_args_list
    assert len(calls) == 3
    assert calls[0].kwargs["model"] == MODEL_FALLBACK_CHAIN[0]
    assert calls[1].kwargs["model"] == MODEL_FALLBACK_CHAIN[1]
    assert calls[2].kwargs["model"] == MODEL_FALLBACK_CHAIN[2]


@patch("app.llm.gemini._get_client")
@patch("app.llm.gemini._wait_for_rate_limit")
@patch("time.sleep")
def test_model_fallback_chain_per_minute_limit(mock_sleep, mock_wait, mock_get_client):
    """
    Test 2: Per-minute 429 on model 1 triggers backoff-retry on THAT SAME model first,
    succeeding on attempt 2 without skipping to model 2.
    """
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    per_minute_exc = Exception(
        "429 RESOURCE_EXHAUSTED. Rate limit exceeded: 15 PerMinute (RPM). Please retry in 1s."
    )

    call_count = 0

    def side_effect(model, contents, config):
        nonlocal call_count
        call_count += 1
        if model == MODEL_FALLBACK_CHAIN[0]:
            if call_count == 1:
                raise per_minute_exc
            else:
                resp = MagicMock()
                resp.text = '{"question": "How do embeddings work?", "type": "conceptual"}'
                return resp
        raise Exception(f"Unexpected model call: {model}")

    mock_client.models.generate_content.side_effect = side_effect

    res = gemini.generate_structured(
        prompt="Test prompt",
        system_instruction="Test system",
    )

    assert res["question"] == "How do embeddings work?"
    assert res["_model_used"] == MODEL_FALLBACK_CHAIN[0]

    # Verify model 1 was retried (2 calls on model 1, 0 calls on model 2)
    calls = mock_client.models.generate_content.call_args_list
    assert len(calls) == 2
    assert calls[0].kwargs["model"] == MODEL_FALLBACK_CHAIN[0]
    assert calls[1].kwargs["model"] == MODEL_FALLBACK_CHAIN[0]
    assert mock_sleep.called
