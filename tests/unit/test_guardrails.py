"""
Unit tests for deterministic PII guardrails and credential sanitization.
"""

from src.guardrails.pii_sanitizer import sanitize_text_and_extract_violations


def test_sanitize_credit_card_masking():
    raw_text = "Customer provided credit card 4111-2222-3333-4444 for verification."
    sanitized, violations = sanitize_text_and_extract_violations(raw_text)

    assert "[REDACTED_CREDIT_CARD]" in sanitized
    assert "4111-2222-3333-4444" not in sanitized
    assert len(violations) == 1
    assert violations[0].field_type == "CREDIT_CARD"
    assert violations[0].severity == "CRITICAL"
    assert violations[0].masked_value == "****-****-****-4444"


def test_sanitize_api_key_masking():
    raw_text = "Developer accidentally logged credentials: AIzaSyA1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q and sk-abc12345678901234567890"
    sanitized, violations = sanitize_text_and_extract_violations(raw_text)

    assert "[REDACTED_API_KEY]" in sanitized
    assert "AIzaSy" not in sanitized
    assert "sk-abc12345678901234567890" not in sanitized
    assert len(violations) == 2
    for v in violations:
        assert v.field_type == "API_KEY"
        assert v.severity == "CRITICAL"


def test_sanitize_cpf_masking():
    raw_text = "The user national ID is 123.456.789-00 recorded in database."
    sanitized, violations = sanitize_text_and_extract_violations(raw_text)

    assert "[REDACTED_CPF]" in sanitized
    assert "123.456.789-00" not in sanitized
    assert len(violations) == 1
    assert violations[0].field_type == "CPF"
    assert violations[0].severity == "HIGH"
    assert violations[0].masked_value == "123.***.***-**"


def test_sanitize_multiple_pii_entities():
    raw_text = "Contact user@example.com at +55 21 99888-7777 with CPF 000.111.222-33."
    sanitized, violations = sanitize_text_and_extract_violations(raw_text)

    assert "[REDACTED_EMAIL]" in sanitized
    assert "[REDACTED_PHONE]" in sanitized
    assert "[REDACTED_CPF]" in sanitized
    assert len(violations) == 3

    types = {v.field_type for v in violations}
    assert types == {"EMAIL", "PHONE", "CPF"}


def test_clean_text_has_zero_violations():
    raw_text = "Standard support interaction regarding password reset and account unlock."
    sanitized, violations = sanitize_text_and_extract_violations(raw_text)

    assert sanitized == raw_text
    assert len(violations) == 0
