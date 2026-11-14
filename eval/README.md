# Compliance Evaluation & Latency Benchmark Suite

This directory verifies the deterministic safety guarantees and latency SLA targets of `qualityops-ai-agent`:

1. **Offline Guardrail & Override Verification (`--mock`):**
   Exercises pre-LLM RegEx PII redaction, chemical hazard boundary detection, and post-LLM deterministic safety overrides (verifying that even a lenient mocked LLM score of `88` is overridden to `score=30`, `security_violation=True`, and `HITLTrigger(priority="CRITICAL")` when critical PII leaks occur). Reports deterministic `guardrail_p50_latency_ms` / `guardrail_p95_latency_ms` while keeping `live_lcel_p95_latency_ms` and `all_under_2s_sla` as `null` (`sla_verified_live: false`) so mocked execution is never conflated with live LLM network telemetry:
   ```bash
   python eval/evaluate.py --dataset eval/dataset/compliance_v1.jsonl --mock
   ```
2. **Live Gemini 2.5 Flash Latency Benchmark:**
   Requires `GEMINI_API_KEY` in `.env` and verifies real single-pass LCEL inference latency (`live_lcel_p95_latency_ms`) against the `< 2.0s` (`2000ms`) target (`sla_verified_live: true`):
   ```bash
   python eval/evaluate.py --dataset eval/dataset/compliance_v1.jsonl
   ```
