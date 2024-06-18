"""
Enterprise compliance audit engine utilizing LangChain LCEL and Google Gemini.
Executes deterministic PII guardrails, structured LCEL evaluation (<2.0s latency),
and conditional Human-in-the-Loop (HITL) supervisory routing for field service operations.
"""

import logging
import os
import re
import time

from dotenv import load_dotenv
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from src.guardrails.pii_sanitizer import sanitize_text_and_extract_violations
from src.models.schemas import AuditReport, AuditRequest, HITLTrigger

load_dotenv()
logger = logging.getLogger("qualityops.audit_engine")

HAZARD_KEYWORDS_PATTERN = re.compile(
    r"\b(chemical|corrosive|toxic|spill|leak|hazard|explosion|flammable|chlorine|ammonia)\b",
    re.IGNORECASE
)

AUDIT_PROMPT_TEMPLATE = """You are QualityOps AI, an enterprise compliance and information security auditor for customer support and field operations.

Analyze the following sanitized support conversation:
----------------------------------------
{sanitized_conversation}
----------------------------------------

Evaluate the representative's performance against:
1. Identity verification protocols before disclosing sensitive data (LGPD / GDPR / internal compliance).
2. Adherence to operational security protocols (PCI-DSS standards for payment data, credentials, PINs).
3. Field safety, chemical hazard awareness, professionalism, and problem resolution quality.

You MUST respond strictly in valid JSON format with the following exact keys:
{{
    "score": <integer from 0 to 100>,
    "security_violation": <true if a security/compliance breach occurred, false otherwise>,
    "violations": [<list of strings detailing detected infractions>],
    "coaching_feedback": "<actionable constructive guidance for the representative>",
    "corrected_response": "<recommended safe and compliant phrasing for the representative>",
    "eval_metric_pass": <true if score >= 70 and security_violation is false, else false>
}}
"""


def _evaluate_hitl_escalation(
    score: int,
    security_violation: bool,
    detected_pii: list,
    conversation_text: str
) -> HITLTrigger:
    has_critical_pii = any(item.severity == "CRITICAL" for item in detected_pii)
    if has_critical_pii:
        return HITLTrigger(
            required=True,
            reason="Critical PII leak detected: immediate security team intervention mandated",
            priority="CRITICAL"
        )

    if HAZARD_KEYWORDS_PATTERN.search(conversation_text):
        return HITLTrigger(
            required=True,
            reason="Field safety hazard or chemical handling protocol deviation detected",
            priority="CRITICAL"
        )

    if security_violation or score < 50:
        return HITLTrigger(
            required=True,
            reason="Operational compliance violation or non-passing audit score (<50)",
            priority="HIGH"
        )

    return HITLTrigger(required=False, reason=None, priority="NONE")


def execute_compliance_audit(request: AuditRequest) -> AuditReport:
    """
    Executes the compliance audit pipeline:
    1. Interception and sanitization of PII via deterministic guardrails.
    2. Contextual compliance evaluation via Gemini 2.5 Flash LCEL chain.
    3. Evaluation of Human-in-the-Loop (HITL) escalation rules.
    4. Strict validation of output against Pydantic AuditReport schema with latency metrics.
    """
    start_time = time.perf_counter()
    sanitized_text, detected_pii = sanitize_text_and_extract_violations(request.conversation_text)
    has_critical_pii = any(item.severity == "CRITICAL" for item in detected_pii)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY not found. Returning structured environment fallback.")
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        hitl = _evaluate_hitl_escalation(0, True, detected_pii, request.conversation_text)
        return AuditReport(
            score=0,
            security_violation=True,
            pii_detected=detected_pii,
            violations=["Missing environment configuration: GEMINI_API_KEY"],
            coaching_feedback="Please configure GEMINI_API_KEY in .env or environment variables before running audits.",
            corrected_response="N/A",
            eval_metric_pass=False,
            latency_ms=elapsed_ms,
            hitl_trigger=hitl
        )

    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
            temperature=0.0,
            max_retries=2
        )

        prompt = PromptTemplate(
            template=AUDIT_PROMPT_TEMPLATE,
            input_variables=["sanitized_conversation"]
        )

        parser = JsonOutputParser()
        chain = prompt | llm | parser

        raw_result = chain.invoke({"sanitized_conversation": sanitized_text})
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        score = int(raw_result.get("score", 50))
        security_violation = bool(raw_result.get("security_violation", has_critical_pii))
        eval_pass = bool(raw_result.get("eval_metric_pass", False))

        if has_critical_pii and score > 40:
            score = 30
            security_violation = True
            eval_pass = False

        hitl = _evaluate_hitl_escalation(score, security_violation, detected_pii, request.conversation_text)

        return AuditReport(
            score=score,
            security_violation=security_violation,
            pii_detected=detected_pii,
            violations=raw_result.get("violations", []),
            coaching_feedback=str(raw_result.get("coaching_feedback", "")),
            corrected_response=str(raw_result.get("corrected_response", "")),
            eval_metric_pass=eval_pass,
            latency_ms=elapsed_ms,
            hitl_trigger=hitl
        )

    except Exception as exc:
        logger.error("Audit pipeline execution failed: %s", exc, exc_info=True)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        hitl = _evaluate_hitl_escalation(0, True, detected_pii, request.conversation_text)
        return AuditReport(
            score=0,
            security_violation=True,
            pii_detected=detected_pii,
            violations=[f"Inference pipeline failure: {exc!s}"],
            coaching_feedback="The audit pipeline encountered an execution error. Please retry.",
            corrected_response="N/A",
            eval_metric_pass=False,
            latency_ms=elapsed_ms,
            hitl_trigger=hitl
        )


def run_audit_chain(chat_text: str) -> dict:
    """
    Backward-compatible entrypoint for Streamlit UI integration.
    Wraps execute_compliance_audit and serializes output to dictionary.
    """
    req = AuditRequest(conversation_text=chat_text)
    report = execute_compliance_audit(req)
    return report.model_dump()
