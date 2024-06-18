"""
Pytest global fixtures and test configuration for QualityOps AI test suite.
"""

from pathlib import Path
import sys

# Ensure repository root is on sys.path for direct pytest CLI invocations
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from src.models.schemas import AuditRequest


@pytest.fixture
def sample_clean_conversation():
    """Compliant customer interaction following standard verification protocols."""
    return AuditRequest(
        conversation_text=(
            "Agent: Hello! Before we proceed, could you please confirm the last 4 digits of your postal code?\n"
            "Customer: Sure, it is 4810.\n"
            "Agent: Identity confirmed. How can I help you with your account today?\n"
            "Customer: I just wanted to verify my billing statement due date.\n"
            "Agent: Your statement is due on the 15th. I have emailed a copy to your verified address."
        ),
        channel="chat_support"
    )


@pytest.fixture
def sample_pii_violation_conversation():
    """Customer interaction containing critical security and PII violations."""
    return AuditRequest(
        conversation_text=(
            "Agent: Please share your tax ID and credit card details so I can check your file.\n"
            "Customer: My CPF is 123.456.789-00 and my card is 4532-1111-2222-3333 with exp 12/28.\n"
            "Agent: Got it, I wrote it down on an unencrypted sticky note."
        ),
        channel="chat_support"
    )


@pytest.fixture
def mock_gemini_chain_response():
    """Deterministic mock response for LangChain + Gemini audit chain."""
    return {
        "score": 95,
        "security_violation": False,
        "violations": [],
        "coaching_feedback": "Excellent identity verification and clear communication.",
        "corrected_response": "Standard compliant behavior maintained.",
        "eval_metric_pass": True
    }
