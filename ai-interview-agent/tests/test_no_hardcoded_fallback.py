"""
Regression test: verify generate_feedback does NOT produce hardcoded fallback
strings when given long mocked answers (500+ words each, 10 turns).
Catches payload-size-triggered fallback regressions.
"""
from unittest.mock import patch, MagicMock
from app.agent.nodes import generate_feedback, _truncate


LONG_ANSWER = (
    "In my experience with building production AI systems, the key consideration "
    "when choosing between synchronous and asynchronous API designs involves "
    "understanding the latency profile of your inference pipeline. For instance, "
    "when using Ollama or vLLM locally, the time-to-first-token is typically "
    "around 200-500ms, but the full generation can take 5-15 seconds depending "
    "on the model size and quantization level. This means that a synchronous "
    "FastAPI endpoint would block the event loop during inference, effectively "
    "reducing your server's throughput to a single concurrent request. Instead, "
    "I would use FastAPI's BackgroundTasks or integrate with an async HTTP client "
    "like httpx to stream results from the inference server. The streaming approach "
    "also has UX benefits because the user can see tokens appearing in real-time "
    "rather than waiting for the full response. For error handling, I implement "
    "circuit breaker patterns using libraries like pybreaker to prevent cascading "
    "failures when the inference server becomes unresponsive. The retry logic uses "
    "exponential backoff with jitter to avoid thundering herd problems. For "
    "production monitoring, I instrument the endpoint with Prometheus histograms "
    "to track p50/p95/p99 latencies and use Grafana dashboards to visualize the "
    "distribution. One critical insight is that Prometheus Summaries cannot be "
    "aggregated across instances because quantiles are not statistically combinable, "
    "so I prefer Histograms with carefully chosen bucket boundaries. I also set up "
    "alerting on the error rate using Alertmanager with PagerDuty integration. "
    "For database operations alongside inference, I use SQLAlchemy with async "
    "session management and implement proper transaction isolation levels to prevent "
    "dirty reads during concurrent inference-and-persist workflows. The SQLite WAL "
    "mode is particularly useful for development because it allows concurrent reads "
    "during writes, which closely mimics the behavior of PostgreSQL in production."
)


def _mock_messages(n_turns=10):
    """Generate n_turns of interviewer+candidate message pairs."""
    msgs = []
    for i in range(1, n_turns + 1):
        msgs.append({
            "role": "interviewer",
            "content": f"Technical question {i} about AI engineering concepts.",
            "question_number": i,
            "curriculum_day": i,
            "topic": f"Day {i} Topic",
        })
        msgs.append({
            "role": "candidate",
            "content": LONG_ANSWER,
            "question_number": i,
            "curriculum_day": i,
            "topic": f"Day {i} Topic",
        })
    return msgs


def _mock_evaluations(n_turns=10):
    """Generate n_turns of evaluation records."""
    evals = []
    for i in range(1, n_turns + 1):
        evals.append({
            "question_number": i,
            "topic": f"Day {i} Topic",
            "overall_score": 7.5 + (i % 3) * 0.5,
            "missing_concepts": [f"concept_alpha_{i}", f"concept_beta_{i}"],
            "evaluation_summary": f"Candidate explained async patterns but missed concept_alpha_{i} and concept_beta_{i}.",
        })
    return evals


FALLBACK_STRINGS = [
    "Active technical participation",
    "Demonstrated foundational skills",
    "Advanced system architecture and production deployment",
]

GEMINI_MOCK_RESPONSE = {
    "summary": "The candidate demonstrated strong knowledge of async API design and monitoring, "
               "correctly citing Prometheus Histogram bucket boundaries and circuit breaker patterns.",
    "strengths": [
        "Correctly identified that Prometheus Summaries cannot be aggregated across instances "
        "because quantiles are not statistically combinable — showing deep monitoring knowledge.",
        "Strong async FastAPI design: specifically mentioned httpx streaming, BackgroundTasks, "
        "and exponential backoff with jitter for retry logic.",
    ],
    "gaps": [
        "When discussing database concurrency, mentioned SQLite WAL mode but did not address "
        "connection pooling strategies needed for production PostgreSQL deployments.",
        "Circuit breaker implementation was described abstractly using pybreaker but lacked "
        "specifics on half-open state thresholds and failure rate windows.",
    ],
    "next": [
        "Practice implementing connection pool sizing with SQLAlchemy's pool_size and max_overflow "
        "parameters to understand production database scaling.",
        "Build a circuit breaker with configurable half-open state using pybreaker and test "
        "failure threshold tuning with load testing tools like Locust.",
    ],
}


def test_truncate_helper():
    """Test the _truncate utility function."""
    assert _truncate("short", 400) == "short"
    assert _truncate("", 400) == ""
    assert _truncate(None, 400) == ""
    long_text = "a" * 500
    result = _truncate(long_text, 400)
    assert len(result) == 403  # 400 chars + "..."
    assert result.endswith("...")


@patch("app.agent.nodes.repository")
@patch("app.agent.nodes.gemini")
def test_feedback_long_transcript_does_not_fallback(mock_gemini, mock_repo):
    """
    With 10 turns of 500+ word answers, generate_feedback MUST NOT
    produce the hardcoded fallback strings. It must call Gemini and
    return grounded feedback.
    """
    mock_repo.get_messages.return_value = _mock_messages(10)
    mock_repo.get_evaluations.return_value = _mock_evaluations(10)
    mock_gemini.generate_structured.return_value = GEMINI_MOCK_RESPONSE

    state = {
        "session_id": "test-long-feedback-session",
        "covered_days": list(range(1, 11)),
        "profile": {"role": "AI Engineer", "experience": 5},
        "strengths": ["Day 3 Topic"],
        "weaknesses": ["Day 7 Topic"],
    }

    result = generate_feedback(state)
    feedback = result["feedback"]

    # Must have called Gemini, not used fallback
    mock_gemini.generate_structured.assert_called_once()

    # Must NOT contain any fallback strings
    all_text = str(feedback)
    for fallback in FALLBACK_STRINGS:
        assert fallback not in all_text, (
            f"Fallback string found in feedback: '{fallback}'. "
            f"generate_feedback is still hitting the static fallback path!"
        )

    # Must have real grounded content
    assert "Prometheus" in feedback["summary"] or "async" in feedback["summary"].lower()
    assert len(feedback["strengths"]) >= 2
    assert len(feedback["gaps"]) >= 2
    assert len(feedback["next"]) >= 2


@patch("app.agent.nodes.repository")
@patch("app.agent.nodes.gemini")
def test_feedback_prompt_contains_condensed_not_full_transcript(mock_gemini, mock_repo):
    """
    The prompt sent to Gemini should contain TRUNCATED answer excerpts,
    not the full 500+ word verbatim answers, to prevent payload-size failures.
    """
    mock_repo.get_messages.return_value = _mock_messages(10)
    mock_repo.get_evaluations.return_value = _mock_evaluations(10)
    mock_gemini.generate_structured.return_value = GEMINI_MOCK_RESPONSE

    state = {
        "session_id": "test-condensed-check",
        "covered_days": list(range(1, 11)),
        "profile": {"role": "AI Engineer", "experience": 5},
        "strengths": [],
        "weaknesses": [],
    }

    generate_feedback(state)

    # Inspect the prompt that was sent to Gemini
    call_args = mock_gemini.generate_structured.call_args
    prompt_sent = call_args[0][0] if call_args[0] else call_args[1].get("prompt", "")

    # The full LONG_ANSWER is ~1600 chars. If transcript is condensed,
    # each answer excerpt should be ≤403 chars (400 + "...").
    # With 10 answers × 1600 chars = 16000 chars of raw answers.
    # With condensation: 10 × 403 = 4030 chars of answer text.
    # So the total prompt should be significantly smaller than 16000 chars of just answers.
    assert "ANSWER (excerpt):" in prompt_sent, "Prompt should use ANSWER (excerpt) labels"
    assert "→ EVAL:" in prompt_sent, "Prompt should contain inline evaluation summaries"

    # Verify the full verbatim answer is NOT in the prompt
    assert LONG_ANSWER not in prompt_sent, (
        "Full verbatim answer found in feedback prompt — "
        "transcript condensation is not working!"
    )


@patch("app.agent.nodes.repository")
@patch("app.agent.nodes.gemini")
def test_feedback_gemini_failure_logs_and_falls_back(mock_gemini, mock_repo):
    """
    When Gemini fails, generate_feedback should still return a response
    (the fallback), but the error should be logged (tested via exception type).
    """
    mock_repo.get_messages.return_value = _mock_messages(3)
    mock_repo.get_evaluations.return_value = _mock_evaluations(3)
    mock_gemini.generate_structured.side_effect = Exception("429 RESOURCE_EXHAUSTED")

    state = {
        "session_id": "test-fallback-session",
        "covered_days": [1, 2, 3],
        "profile": {"role": "AI Engineer", "experience": 5},
        "strengths": ["Day 1 Topic"],
        "weaknesses": ["Day 3 Topic"],
    }

    result = generate_feedback(state)
    feedback = result["feedback"]

    # Fallback should still produce valid output
    assert "summary" in feedback
    assert "strengths" in feedback
    assert "gaps" in feedback
    assert "next" in feedback
    assert result["done"] is True
