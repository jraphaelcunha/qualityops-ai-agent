"""
Evaluation harness for QualityOps AI compliance pipeline.

Strictly separates deterministic guardrail & latency verification (--mock) from live
Gemini 2.5 Flash API execution, verifying zero-false-negative PII/hazard safety overrides
and sub-2.0s execution SLA targets.
"""

import argparse
import json
import math
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.guardrails.pii_sanitizer import sanitize_text_and_extract_violations
from src.langchain_backend import execute_compliance_audit
from src.models.schemas import AuditRequest


@dataclass
class ComplianceEvalSample:
    """Single sample verification record."""

    sample_id: str
    category: str
    pii_recall_exact: bool
    hitl_match: bool
    override_enforced: bool
    guardrail_latency_ms: float
    live_lcel_latency_ms: float | None
    under_2s_sla: bool | None


@dataclass
class ComplianceEvalSummary:
    """Aggregated evaluation report for compliance guardrails and LCEL performance."""

    mode: str
    total_samples: int
    pii_detection_accuracy: float
    hitl_accuracy: float
    critical_override_accuracy: float
    guardrail_p50_latency_ms: float
    guardrail_p95_latency_ms: float
    live_lcel_p50_latency_ms: float | None
    live_lcel_p95_latency_ms: float | None
    sla_verified_live: bool
    all_under_2s_sla: bool | None
    results: list[ComplianceEvalSample] = field(default_factory=list)


def compute_percentile(values: list[float], percentile: float) -> float:
    """Compute percentile via linear interpolation."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    k = (len(sorted_vals) - 1) * (percentile / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return round(sorted_vals[int(k)], 3)
    d0 = sorted_vals[int(f)] * (c - k)
    d1 = sorted_vals[int(c)] * (k - f)
    return round(d0 + d1, 3)


def run_evaluation(
    dataset_path: str | Path,
    *,
    force_mock: bool = True,
) -> ComplianceEvalSummary:
    """Execute deterministic guardrail + LCEL evaluation (--mock) or live Gemini benchmark."""
    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(f"Compliance evaluation dataset not found: {path}")

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not force_mock and not api_key:
        raise RuntimeError(
            "Live evaluation requested without GEMINI_API_KEY configured. "
            "Pass --mock for offline deterministic verification."
        )

    results: list[ComplianceEvalSample] = []
    guardrail_latencies: list[float] = []
    live_latencies: list[float] = []

    with open(path, encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            record = json.loads(stripped)
            text = record["conversation_text"]

            # Verify pre-LLM RegEx sanitizer independently and time guardrail execution
            guard_start = time.perf_counter()
            _, detected_pii = sanitize_text_and_extract_violations(text)
            guardrail_ms = round((time.perf_counter() - guard_start) * 1000, 3)

            detected_types = sorted({item.field_type for item in detected_pii})
            expected_types = sorted(record.get("expected_pii_types", []))
            pii_exact = detected_types == expected_types

            req = AuditRequest(conversation_text=text, channel="eval_harness")

            if force_mock:
                mock_payload = record["mock_llm_response"]
                start = time.perf_counter()
                with (
                    patch.dict(os.environ, {"GEMINI_API_KEY": "eval_mock_key"}),
                    patch("src.langchain_backend.ChatGoogleGenerativeAI"),
                    patch("langchain_core.prompts.PromptTemplate.__or__") as mock_pipe,
                ):
                    mock_chain = mock_pipe.return_value.__or__.return_value
                    mock_chain.invoke.return_value = mock_payload
                    report = execute_compliance_audit(req)
                elapsed_ms = round((time.perf_counter() - start) * 1000, 3)
                guardrail_latencies.append(elapsed_ms)
                sample_live_ms: float | None = None
                sample_sla: bool | None = None
            else:
                guardrail_latencies.append(guardrail_ms)
                start = time.perf_counter()
                report = execute_compliance_audit(req)
                elapsed_ms = round((time.perf_counter() - start) * 1000, 3)
                live_latencies.append(elapsed_ms)
                sample_live_ms = elapsed_ms
                sample_sla = elapsed_ms < 2000.0

            expect_hitl = bool(record["expect_hitl"])
            hitl_match = report.hitl_trigger.required == expect_hitl

            expect_override = bool(record["expect_critical_override"])
            if expect_override:
                override_ok = (
                    report.hitl_trigger.required is True
                    and report.hitl_trigger.priority == "CRITICAL"
                    and (not any(p.severity == "CRITICAL" for p in detected_pii) or report.score <= 30)
                )
            else:
                override_ok = True

            results.append(
                ComplianceEvalSample(
                    sample_id=record["id"],
                    category=record["category"],
                    pii_recall_exact=pii_exact,
                    hitl_match=hitl_match,
                    override_enforced=override_ok,
                    guardrail_latency_ms=elapsed_ms if force_mock else guardrail_ms,
                    live_lcel_latency_ms=sample_live_ms,
                    under_2s_sla=sample_sla,
                )
            )

    total = len(results)
    pii_hits = sum(1 for r in results if r.pii_recall_exact)
    hitl_hits = sum(1 for r in results if r.hitl_match)
    override_hits = sum(1 for r in results if r.override_enforced)

    return ComplianceEvalSummary(
        mode="offline_guardrail_and_lcel_mock" if force_mock else "live_gemini_2_5_flash",
        total_samples=total,
        pii_detection_accuracy=round(pii_hits / total, 4) if total else 0.0,
        hitl_accuracy=round(hitl_hits / total, 4) if total else 0.0,
        critical_override_accuracy=round(override_hits / total, 4) if total else 0.0,
        guardrail_p50_latency_ms=compute_percentile(guardrail_latencies, 50),
        guardrail_p95_latency_ms=compute_percentile(guardrail_latencies, 95),
        live_lcel_p50_latency_ms=None if force_mock else compute_percentile(live_latencies, 50),
        live_lcel_p95_latency_ms=None if force_mock else compute_percentile(live_latencies, 95),
        sla_verified_live=not force_mock,
        all_under_2s_sla=None if force_mock else all(bool(r.under_2s_sla) for r in results),
        results=results,
    )


def main() -> None:
    """CLI entrypoint for QualityOps evaluation harness."""
    parser = argparse.ArgumentParser(
        description="Evaluate QualityOps AI Guardrails, Overrides & LCEL Latency"
    )
    parser.add_argument(
        "--dataset",
        default="eval/dataset/compliance_v1.jsonl",
        help="Path to JSONL compliance dataset",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run deterministic offline guardrail and mocked LCEL verification",
    )
    args = parser.parse_args()

    summary = run_evaluation(args.dataset, force_mock=args.mock)
    print(json.dumps(asdict(summary), indent=2))


if __name__ == "__main__":
    main()
