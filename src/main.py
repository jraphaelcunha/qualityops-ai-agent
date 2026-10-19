import json
import logging
import os
import re
import signal
import sys

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()
os.environ["OPENAI_API_KEY"] = "NA" # Dummy key to bypass CrewAI check

# Windows compatibility patch for crewai
if sys.platform.startswith("win"):
    if not hasattr(signal, "SIGHUP"):
        signal.SIGHUP = 1  # Dummy value
    if not hasattr(signal, "SIGQUIT"):
        signal.SIGQUIT = 3 # Dummy value
    if not hasattr(signal, "SIGCONT"):
        signal.SIGCONT = 18 # Dummy value
    if not hasattr(signal, "SIGTSTP"):
        signal.SIGTSTP = 20 # Dummy value

# Add src to pythonpath
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.agents.crew import create_compliance_crew

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
LOGS_PATH = os.path.join(DATA_DIR, "mock_chat_logs.json")

def load_logs():
    with open(LOGS_PATH, 'r') as f:
        return json.load(f)

def clean_and_parse_json(raw_output):
    """
    Robust parser that handles JSON, Markdown, and Python-string formats.
    """
    try:
        text = str(raw_output).strip()

        # 1. Try Standard JSON Parsing first
        # Extract content between first { and last }
        json_match = re.search(r'(\{.*\})', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except (json.JSONDecodeError, ValueError) as decode_err:
                logger.debug("Failed to decode JSON block, attempting fallback: %s", decode_err)

        # 2. Try Handling Python String Representation (The error we saw)
        # Format: score=5 security_violation=True ...
        if "score=" in text:
            data = {}

            # Extract Score
            s_match = re.search(r'score=(\d+)', text)
            if s_match:
                data['score'] = int(s_match.group(1))
            else:
                data['score'] = 0

            # Extract Security Violation
            sec_match = re.search(r'security_violation=(True|False)', text, re.IGNORECASE)
            if sec_match:
                data['security_violation'] = (sec_match.group(1).lower() == 'true')
            else:
                data['security_violation'] = True

            # Extract Violations (Simple Regex)
            v_match = re.search(r"violations=\['(.*?)'\]", text)
            if v_match:
                data['violations'] = [v_match.group(1)]
            else:
                # Fallback if list format is complex, just grab the text line
                data['violations'] = ["Security Protocol Violation Detected (See raw output for details)"]

            data['coaching_feedback'] = "Agent detected a security failure (PIN verification)."
            data['corrected_response'] = "Please ask for the PIN before proceeding."

            return data

        # 3. Last Resort: Auto-Fail if we can't parse but know it's not empty
        return {
            "score": 0,
            "security_violation": True,
            "violations": ["Output Format Error (Raw data received but not parsed)"],
            "coaching_feedback": f"Raw content: {text[:100]}...",
            "corrected_response": "System Error"
        }

    except (json.JSONDecodeError, ValueError, TypeError, KeyError) as e:
        logger.warning("PARSING FAILED: %s", e)
        return None

def run_audit():
    print("Use 'streamlit run src/app.py' for the UI.")

def run_single_audit(chat_text: str) -> dict:
    print("\n\n🔵 STARTING AUDIT FOR TEXT:")
    print(chat_text[:50] + "...")

    try:
        crew = create_compliance_crew(chat_text)
        result = crew.kickoff()

        # Clean and Parse
        parsed_result = clean_and_parse_json(result)

        if parsed_result:
            print("Audit processed successfully.")
            return parsed_result
        else:
            # Fallback if parsing fails completely
            print("⚠️ RETURNING FALLBACK ERROR DICT")
            return {
                "score": 0,
                "security_violation": True,
                "violations": ["System Error: Could not parse Agent output.", f"Raw Output: {str(result)[:100]}..."],
                "coaching_feedback": "Please check terminal logs for raw output.",
                "corrected_response": "N/A"
            }

    except Exception as e:  # noqa: BLE001 - CLI top-level boundary exception handler
        print(f"🔴 CRITICAL ERROR IN MAIN: {e!s}")
        error_str = str(e)

        # Friendly error for API Key issues
        if "API key expired" in error_str or "API_KEY_INVALID" in error_str or "PERMISSION_DENIED" in error_str:
             return {
                "score": 0,
                "security_violation": True,
                "violations": ["Configuration Error: Google Gemini API Key is expired or invalid.", "Action Required: Update GEMINI_API_KEY in .env file."],
                "coaching_feedback": "System Configuration Required. check your Google AI Studio account.",
                "corrected_response": "N/A"
            }

        return {
            "score": 0,
            "security_violation": True,
            "violations": [f"System Exception: {e!s}"],
            "coaching_feedback": "Contact Technical Support.",
            "corrected_response": "N/A"
        }

if __name__ == "__main__":
    run_audit()
