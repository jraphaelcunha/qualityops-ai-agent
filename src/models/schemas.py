"""
Data contracts and schema definitions for QualityOps AI audit pipelines.
Enforces strict validation, field protection, and serialization using Pydantic v2.
"""

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictBaseSchema(BaseModel):
    """Base schema enforcing strict type validation and prohibiting extra fields."""
    model_config = ConfigDict(strict=True, extra="forbid")

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __getitem__(self, item: str) -> Any:
        if hasattr(self, item):
            return getattr(self, item)
        raise KeyError(item)


class PIIViolation(StrictBaseSchema):
    """Contract for sensitive data detection and leak auditing."""
    field_type: Literal["CPF", "CREDIT_CARD", "PHONE", "EMAIL", "API_KEY", "OTHER"]
    masked_value: str = Field(..., description="Masked value for audit log retention")
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"] = "HIGH"


class HITLTrigger(StrictBaseSchema):
    """Human-in-the-loop operational escalation schema for safety and compliance triggers."""
    required: bool = Field(default=False, description="Whether human supervisory review is required")
    reason: str | None = Field(default=None, description="Escalation cause or compliance policy breach")
    priority: Literal["CRITICAL", "HIGH", "NORMAL", "NONE"] = Field(
        default="NONE",
        description="Queue routing priority for field supervisors"
    )


class AuditRequest(StrictBaseSchema):
    """Input payload for customer conversation compliance validation."""
    conversation_text: str = Field(
        ...,
        min_length=10,
        description="Customer service chat or audio transcription text"
    )
    channel: str = Field(default="customer_support", description="Origin channel (chat, voice, ticket)")
    metadata: dict[str, str] = Field(default_factory=dict, description="Session or agent metadata")


class AuditReport(StrictBaseSchema):
    """Strict output schema for compliance audit reports."""
    score: int = Field(..., ge=0, le=100, description="Compliance score ranging from 0 to 100")
    security_violation: bool = Field(..., description="Flag indicating critical security or compliance breaches")
    pii_detected: list[PIIViolation] = Field(default_factory=list, description="List of detected and intercepted sensitive entities")
    violations: list[str] = Field(default_factory=list, description="Detailed descriptions of violated business or regulatory rules")
    coaching_feedback: str = Field(..., description="Actionable constructive guidance for the representative")
    corrected_response: str = Field(..., description="Recommended safe and compliant phrasing for the representative")
    eval_metric_pass: bool = Field(default=True, description="Quality gate evaluation pass/fail status")
    latency_ms: float = Field(default=0.0, ge=0.0, description="End-to-end execution latency in milliseconds")
    hitl_trigger: HITLTrigger = Field(
        default_factory=lambda: HITLTrigger(required=False, reason=None, priority="NONE"),
        description="Escalation payload for human review queues"
    )
    audited_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC timestamp of audit execution")

    @field_validator("score")
    @classmethod
    def validate_score_range(cls, v: int) -> int:
        if not (0 <= v <= 100):
            raise ValueError("Audit score must be strictly between 0 and 100.")
        return v
