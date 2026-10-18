"""
ARCHITECTURE NOTE: Prototype configuration using LiteLLM/Gemini.
For Production (AWS), switch to BedrockChat and ensure IAM Roles are configured for bedrock:InvokeModel permissions.
"""
import os
import signal
import sys

# Windows compatibility patch for crewai signal handlers
if sys.platform.startswith("win"):
    for sig_name in ("SIGHUP", "SIGQUIT", "SIGCONT", "SIGTSTP"):
        if not hasattr(signal, sig_name):
            setattr(signal, sig_name, 1)

from crewai import Agent, Crew, Process, Task

from src.agents.schemas import ComplianceResult
from src.agents.tools import RulesSearchTool


def validate_gemini_key():
    """Validate that GEMINI_API_KEY is set in environment"""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables. Please set it in .env file.")
    return api_key

def create_compliance_crew(chat_transcription: str) -> Crew:
    # Validate API key is present
    validate_gemini_key()
    print("Using LLM: gemini/gemini-2.5-flash (via LiteLLM)")

    # --- Agents ---
    auditor = Agent(
        role="Compliance Auditor",
        goal="Verify chat logs against support rules found in the knowledge base. FOCUS ON SECURITY (PIN Verification).",
        backstory="You are a strict QA auditor who never misses a security slip. You meticulously check every interaction against the rulebook.",
        tools=[RulesSearchTool()],
        llm="gemini/gemini-2.5-flash",
        verbose=True,
        allow_delegation=False
    )

    coach = Agent(
        role="Senior Support Lead",
        goal="Teach the agent how to improve based on the auditor's findings.",
        backstory="You are a wise mentor. You take the harsh findings of the auditor and turn them into constructive, actionable feedback.",
        llm="gemini/gemini-2.5-flash",
        verbose=True,
        allow_delegation=False
    )

    # --- Tasks ---
    audit_task = Task(
        description=f"""
        Analyze the following chat transcription:
        '{chat_transcription}'

        Search the rules to verify if the agent followed protocol.
        Look specifically for PIN verification failures before account details were discussed.
        Check for any other compliance violations based on the retrieved rules.
        """,
        expected_output="A list of violations and an analysis of the security procedure.",
        agent=auditor
    )

    report_task = Task(
        description="""
        Generate a structured report based on the audit findings.
        Provide a compliance score (0-100).
        Flag if there was a security violation.
        List specific violations.
        Write constructive coaching feedback.
        Rewrite the agent's response to be compliant.
        """,
        expected_output="A structured JSON object matching the ComplianceResult schema.",
        agent=coach,
        context=[audit_task],
        output_pydantic=ComplianceResult
    )

    # --- Crew ---
    crew = Crew(
        agents=[auditor, coach],
        tasks=[audit_task, report_task],
        process=Process.sequential,
        verbose=True,
        memory=False # Disable memory to avoid OpenAI embedding dependency
    )

    return crew
