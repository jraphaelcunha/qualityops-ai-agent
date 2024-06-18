"""
Deterministic PII guardrails and sanitization utilities.
Intercepts and redacts sensitive data (CPF, Credit Card, Email, Phone, API Keys) prior to external LLM calls.
"""

import re

from src.models.schemas import PIIViolation

CPF_PATTERN = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
CREDIT_CARD_PATTERN = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
PHONE_PATTERN = re.compile(r"\b(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)?(?:9\d{4}[-\s]?\d{4}|\d{4}[-\s]?\d{4})\b")
API_KEY_PATTERN = re.compile(r"\b(?:sk-[a-zA-Z0-9_-]{20,}|AIzaSy[a-zA-Z0-9_-]{33}|ghp_[a-zA-Z0-9]{36})\b")


def sanitize_text_and_extract_violations(raw_text: str) -> tuple[str, list[PIIViolation]]:
    """
    Deterministic safety guardrail intercepting sensitive data before external LLM dispatch.
    Returns the sanitized text and structured violation contracts.
    """
    violations: list[PIIViolation] = []
    sanitized = raw_text

    for match in CREDIT_CARD_PATTERN.finditer(sanitized):
        val = match.group(0)
        masked = f"****-****-****-{val[-4:]}" if len(val) >= 4 else "****"
        violations.append(
            PIIViolation(
                field_type="CREDIT_CARD",
                masked_value=masked,
                severity="CRITICAL"
            )
        )
    sanitized = CREDIT_CARD_PATTERN.sub("[REDACTED_CREDIT_CARD]", sanitized)

    for match in API_KEY_PATTERN.finditer(sanitized):
        val = match.group(0)
        masked = f"{val[:4]}...{val[-4:]}" if len(val) >= 8 else "****"
        violations.append(
            PIIViolation(
                field_type="API_KEY",
                masked_value=masked,
                severity="CRITICAL"
            )
        )
    sanitized = API_KEY_PATTERN.sub("[REDACTED_API_KEY]", sanitized)

    for match in CPF_PATTERN.finditer(sanitized):
        val = match.group(0)
        masked = f"{val[:3]}.***.***-**"
        violations.append(
            PIIViolation(
                field_type="CPF",
                masked_value=masked,
                severity="HIGH"
            )
        )
    sanitized = CPF_PATTERN.sub("[REDACTED_CPF]", sanitized)

    for match in EMAIL_PATTERN.finditer(sanitized):
        val = match.group(0)
        parts = val.split("@")
        masked = f"{parts[0][:2]}***@{parts[1]}" if len(parts) == 2 else "***@***"
        violations.append(
            PIIViolation(
                field_type="EMAIL",
                masked_value=masked,
                severity="MEDIUM"
            )
        )
    sanitized = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", sanitized)

    for match in PHONE_PATTERN.finditer(sanitized):
        val = match.group(0)
        masked = f"{val[:4]}****{val[-2:]}" if len(val) >= 6 else "****"
        violations.append(
            PIIViolation(
                field_type="PHONE",
                masked_value=masked,
                severity="MEDIUM"
            )
        )
    sanitized = PHONE_PATTERN.sub("[REDACTED_PHONE]", sanitized)

    return sanitized, violations
