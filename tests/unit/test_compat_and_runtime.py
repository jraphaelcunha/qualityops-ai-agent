"""
Unit tests for platform compatibility, signal cleanliness, and graceful runtime fallbacks.
"""

import signal
import sys
from unittest.mock import MagicMock

import pytest

import src.agents.crew as crew_module
import src.agents.tools as tools_module
import src.main as main_module
import src.rag.ingest as ingest_module
import src.rag.retriever as retriever_module


def test_signal_module_is_unpolluted_on_windows():
    """Verify that Python's standard library signal module is not mutated with artificial signals."""
    if sys.platform.startswith("win"):
        # On native Windows, signal does not define SIGHUP or SIGQUIT
        # The codebase must NOT inject dummy integer attributes onto signal
        sighup = getattr(signal, "SIGHUP", None)
        sigquit = getattr(signal, "SIGQUIT", None)
        assert sighup is None or isinstance(sighup, signal.Signals)
        assert sigquit is None or isinstance(sigquit, signal.Signals)


def test_import_main_and_crew_succeeds_cleanly():
    """Verify that importing src.main and src.agents.crew succeeds without errors."""
    assert main_module is not None
    assert crew_module is not None
    assert tools_module is not None
    assert retriever_module is not None
    assert ingest_module is not None


def test_validate_gemini_key_behavior(monkeypatch):
    """Verify that validate_gemini_key enforces presence and returns valid key."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="GEMINI_API_KEY not found in environment variables"):
        crew_module.validate_gemini_key()

    monkeypatch.setenv("GEMINI_API_KEY", "test_mock_key_value")
    assert crew_module.validate_gemini_key() == "test_mock_key_value"


def test_create_compliance_crew_graceful_check(monkeypatch):
    """Verify create_compliance_crew behavior when crewai is unavailable vs mocked."""
    monkeypatch.setenv("GEMINI_API_KEY", "test_mock_key")

    # When crewai is unavailable
    monkeypatch.setattr(crew_module, "_CREWAI_AVAILABLE", False)
    with pytest.raises(RuntimeError, match="CrewAI is not available"):
        crew_module.create_compliance_crew("Sample transcription text")


def test_create_compliance_crew_mocked_initialization(monkeypatch):
    """Verify create_compliance_crew initialization when crewai classes are provided (no LLM call)."""
    monkeypatch.setenv("GEMINI_API_KEY", "test_mock_key")
    monkeypatch.setattr(crew_module, "_CREWAI_AVAILABLE", True)

    mock_agent = MagicMock()
    mock_crew = MagicMock()
    mock_task = MagicMock()
    mock_process = MagicMock()

    monkeypatch.setattr(crew_module, "Agent", mock_agent)
    monkeypatch.setattr(crew_module, "Crew", mock_crew)
    monkeypatch.setattr(crew_module, "Task", mock_task)
    monkeypatch.setattr(crew_module, "Process", mock_process)

    result = crew_module.create_compliance_crew("Agent: Hello, can I get your PIN? Customer: 1234")
    assert result == mock_crew.return_value
    assert mock_agent.call_count == 2
    assert mock_task.call_count == 2
    mock_crew.assert_called_once()


def test_clean_and_parse_json_valid_json():
    """Verify clean_and_parse_json successfully parses JSON objects."""
    raw = '{"score": 95, "security_violation": false, "violations": [], "coaching_feedback": "Great job"}'
    parsed = main_module.clean_and_parse_json(raw)
    assert parsed["score"] == 95
    assert not parsed["security_violation"]


def test_clean_and_parse_json_string_format():
    """Verify clean_and_parse_json handles regex fallback for string representation."""
    raw = "score=10 security_violation=True violations=['Failed PIN verification']"
    parsed = main_module.clean_and_parse_json(raw)
    assert parsed["score"] == 10
    assert parsed["security_violation"] is True
    assert parsed["violations"] == ["Failed PIN verification"]


def test_clean_and_parse_json_fallback_error():
    """Verify clean_and_parse_json falls back safely on unparseable garbage."""
    raw = "completely unparseable content without any structure"
    parsed = main_module.clean_and_parse_json(raw)
    assert parsed["score"] == 0
    assert parsed["security_violation"] is True


def test_rag_retriever_graceful_fallback(monkeypatch):
    """Verify query_knowledge_base returns informative message when vectorstore is unavailable."""
    monkeypatch.setattr(retriever_module, "_RAG_AVAILABLE", False)
    res = retriever_module.query_knowledge_base("test query")
    assert "Error:" in res[0]
