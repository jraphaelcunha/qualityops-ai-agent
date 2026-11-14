
import os
import sys

# Fix path to ensure imports work in Streamlit Cloud
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

import streamlit as st

# Now import the backend safely
try:
    import langchain_backend as backend
    run_audit_chain = backend.run_audit_chain
except ImportError as e:
    st.error(f"Critical System Error: {e}")
    st.stop()

# Page Configuration
st.set_page_config(
    page_title="QualityOps Agent",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar
with st.sidebar:
    st.image("https://placehold.co/200x80?text=QualityOps", use_container_width=True)
    st.title("🛡️ QualityOps")
    st.info(
        """
        **System Architecture:**
        * ⚡ **Orchestration:** LangChain LCEL
        * 🧠 **LLM:** Gemini 2.5 Flash
        * 🔍 **Parser:** JsonOutputParser
        """
    )
    st.markdown("---")
    st.caption("Enterprise Edition v2.0")

# Main Content
st.title("Intelligent QA & Compliance Agent")
st.markdown("Automated auditing system for Customer Support. Detects **Security Violations** and ensures **Quality Standards**.")
st.divider()

# Layout
# 4. Input Area (Columns)
col_input, col_actions = st.columns([3, 1])

# initialize session state if not present
if 'chat_input' not in st.session_state:
    st.session_state['chat_input'] = ""

def load_bad_example():
    st.session_state['chat_input'] = """Agent: Hello.
Customer: I want to update my billing address.
Agent: Sure, what is the new address?
Customer: It is 123 Main St.
Agent: Done.
(Context: Agent failed to verify PIN before changing account data)"""

with col_input:
    # Use key='chat_input' directly. Value is not needed.
    st.text_area(
        "📝 Interaction Log",
        height=250,
        placeholder="Paste the chat transcript here...",
        help="Paste the raw text of the conversation.",
        key="chat_input" # Binds directly to st.session_state['chat_input']
    )

with col_actions:
    st.write("### Controls")

    # Callback pattern avoids StreamlitAPIException
    st.button("🚨 Load Bad Example", use_container_width=True, on_click=load_bad_example)

    st.write("")
    run_btn = st.button("▶️ Run Audit", type="primary", use_container_width=True)

# Helper to cache input/output
@st.cache_data(show_spinner=False)
def cached_audit(text):
    return run_audit_chain(text)

# 5. Execution & Dashboard
if run_btn:
    # Use the session state value for the audit
    final_input = st.session_state['chat_input']

    if not final_input or len(final_input) < 10:
        st.warning("⚠️ Please enter a valid chat log (min 10 chars).")
    else:
        with st.spinner("🤖 LangChain Agents are analyzing protocols..."):
            try:
                result = cached_audit(final_input)

                st.divider()
                m1, m2, m3 = st.columns(3)
                score = result.get('score', 0)
                is_violation = result.get('security_violation', False)

                m1.metric("Score", f"{score}/100")
                m2.metric("Security", "FAILED" if is_violation else "PASSED", delta_color="off" if is_violation else "normal")
                m3.metric("Violations", len(result.get('violations', [])))

                tab1, tab2 = st.tabs(["🚫 Violations", "✅ Corrected Response"])
                with tab1:
                    if is_violation:
                        st.error("⚠️ CRITICAL VIOLATION")
                    for v in result.get('violations', []):
                        st.warning(f"❌ {v}")
                    st.info(f"💡 Feedback: {result.get('coaching_feedback')}")
                with tab2:
                    st.code(result.get('corrected_response'))

            except Exception as e:  # noqa: BLE001 - Streamlit UI top-level boundary exception handler
                st.error(f"Error: {e!s}")
