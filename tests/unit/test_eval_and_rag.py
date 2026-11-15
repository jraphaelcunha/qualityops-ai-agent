"""Unit tests for QualityOps evaluation harness and RAG/ingestion fallback guards."""

import pytest

from eval.evaluate import run_evaluation
from src.models.schemas import AuditReport, HITLTrigger
from src.rag import ingest, retriever


def test_offline_compliance_eval_enforces_overrides_and_pii_recall():
    summary = run_evaluation("eval/dataset/compliance_v1.jsonl", force_mock=True)

    assert summary.mode == "offline_guardrail_and_lcel_mock"
    assert summary.total_samples == 6
    assert summary.pii_detection_accuracy == 1.0
    assert summary.hitl_accuracy == 1.0
    assert summary.critical_override_accuracy == 1.0
    assert summary.guardrail_p95_latency_ms < 50.0
    assert summary.live_lcel_p95_latency_ms is None
    assert summary.sla_verified_live is False
    assert summary.all_under_2s_sla is None


def test_live_compliance_eval_refuses_without_gemini_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        run_evaluation("eval/dataset/compliance_v1.jsonl", force_mock=False)


def test_rag_retriever_handles_missing_vectorstore_or_deps(monkeypatch, tmp_path):
    monkeypatch.setattr(retriever, "VECTORSTORE_DIR", str(tmp_path / "missing_vec"))
    res = retriever.query_knowledge_base("PIN verification")
    assert isinstance(res, list)
    assert len(res) == 1
    assert "Error:" in res[0]


def test_rag_ingest_handles_missing_source_or_deps(monkeypatch, tmp_path):
    monkeypatch.setattr(ingest, "SOURCE_FILE", str(tmp_path / "nonexistent.md"))
    assert ingest.ingest_data() is None


def test_eval_harness_fails_override_check_when_hazard_lacks_score_cap(monkeypatch, tmp_path):
    """Evaluation harness must reject expect_critical_override hazard samples if score>30 or violation=False."""
    hazard_dataset = tmp_path / "hazard_only.jsonl"
    hazard_dataset.write_text(
        '{"id": "comp_hazard_test", "category": "chemical_hazard_incident", '
        '"expected_pii_types": [], "expect_hitl": true, "expect_critical_override": true, '
        '"mock_llm_response": {"score": 75, "security_violation": false, "violations": [], '
        '"coaching_feedback": "Normal callback.", "corrected_response": "Hazmat.", '
        '"eval_metric_pass": true}, '
        '"conversation_text": "Customer: Toxic chemical spill with chlorine fumes!"}\n',
        encoding="utf-8",
    )
    fake_unoverridden_report = AuditReport(
        score=75,
        security_violation=False,
        pii_detected=[],
        violations=[],
        coaching_feedback="Normal callback.",
        corrected_response="Hazmat.",
        eval_metric_pass=True,
        latency_ms=1.0,
        hitl_trigger=HITLTrigger(required=True, reason="Hazard", priority="CRITICAL"),
    )
    monkeypatch.setattr(
        "eval.evaluate.execute_compliance_audit",
        lambda _req: fake_unoverridden_report,
    )
    summary = run_evaluation(str(hazard_dataset), force_mock=True)
    assert summary.critical_override_accuracy == 0.0

