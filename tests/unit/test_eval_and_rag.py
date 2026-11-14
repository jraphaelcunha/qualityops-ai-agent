"""Unit tests for QualityOps evaluation harness and RAG/ingestion fallback guards."""

import pytest

from eval.evaluate import run_evaluation
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
