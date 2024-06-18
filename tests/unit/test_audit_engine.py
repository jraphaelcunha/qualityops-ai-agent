"""
Unit tests for audit engine orchestration, LCEL latency tracking, and Pydantic data contracts.
"""

from unittest.mock import patch

from pydantic import ValidationError
import pytest
from src.langchain_backend import execute_compliance_audit
from src.models.schemas import AuditReport, AuditRequest


def test_audit_report_schema_validation():
    """Validate Pydantic v2 schema integrity."""
    report = AuditReport(
        score=85,
        security_violation=False,
        violations=[],
        coaching_feedback="Constructive coaching notes.",
        corrected_response="Maintain compliant protocols.",
        eval_metric_pass=True,
        latency_ms=180.5
    )
    assert report.score == 85
    assert not report.security_violation
    assert report.eval_metric_pass
    assert report.latency_ms == 180.5
    assert report.hitl_trigger.required is False


def test_audit_report_forbids_extra_fields():
    """Validate that extra fields are rejected under Pydantic v2 strict configuration."""
    with pytest.raises(ValidationError):
        AuditReport(
            score=80,
            security_violation=False,
            coaching_feedback="Ok",
            corrected_response="Ok",
            arbitrary_extra_field="malicious_payload"
        )


def test_audit_report_invalid_score_raises_error():
    """Verify that out-of-range audit scores raise validation errors."""
    with pytest.raises(ValidationError):
        AuditReport(
            score=150,
            security_violation=False,
            violations=[],
            coaching_feedback="Error",
            corrected_response="Error",
            eval_metric_pass=False
        )


def test_execute_audit_missing_env_key(sample_clean_conversation, monkeypatch):
    """Verify graceful fallback and HITL routing when GEMINI_API_KEY is not configured."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    report = execute_compliance_audit(sample_clean_conversation)

    assert report.score == 0
    assert report.security_violation is True
    assert "GEMINI_API_KEY" in report.violations[0]
    assert report.eval_metric_pass is False
    assert report.hitl_trigger.required is True
    assert report.latency_ms >= 0.0


def test_execute_audit_hitl_critical_pii_trigger(sample_pii_violation_conversation, monkeypatch):
    """Verify that critical PII leaks automatically activate HITL supervisory queue escalation."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    report = execute_compliance_audit(sample_pii_violation_conversation)

    assert report.hitl_trigger.required is True
    assert report.hitl_trigger.priority == "CRITICAL"
    assert "Critical PII" in str(report.hitl_trigger.reason)


def test_execute_audit_hitl_chemical_hazard_trigger(monkeypatch):
    """Verify that field service chemical hazard incidents trigger critical supervisor review."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    req = AuditRequest(
        conversation_text="Customer reported a toxic chemical spill during pest control service inspection."
    )
    report = execute_compliance_audit(req)

    assert report.hitl_trigger.required is True
    assert report.hitl_trigger.priority == "CRITICAL"
    assert "chemical" in str(report.hitl_trigger.reason).lower() or "hazard" in str(report.hitl_trigger.reason).lower()


@patch("src.langchain_backend.ChatGoogleGenerativeAI")
def test_execute_audit_with_mocked_llm(
    mock_llm_cls,
    sample_clean_conversation,
    mock_gemini_chain_response,
    monkeypatch
):
    """Verify end-to-end audit pipeline execution with mocked LLM (deterministic, sub-2s latency)."""
    monkeypatch.setenv("GEMINI_API_KEY", "mock_key_for_testing")

    with patch("langchain_core.prompts.PromptTemplate.__or__") as mock_pipeline:
        mock_chain = mock_pipeline.return_value.__or__.return_value
        mock_chain.invoke.return_value = mock_gemini_chain_response

        report = execute_compliance_audit(sample_clean_conversation)

        assert report.score == 95
        assert report.security_violation is False
        assert report.eval_metric_pass is True
        assert report.latency_ms >= 0.0
        assert report.hitl_trigger.required is False
        assert "Excellent" in report.coaching_feedback
