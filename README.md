# 🛡️ QualityOps AI — Enterprise Compliance & SRE Audit Platform

[![CI Quality Gate](https://github.com/jraphaelbarbosa/QualityOps-AI-Agent/actions/workflows/ci.yml/badge.svg)](https://github.com/jraphaelbarbosa/QualityOps-AI-Agent)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Pydantic v2](https://img.shields.io/badge/Contracts-Pydantic%20v2-red)
![LangChain](https://img.shields.io/badge/Orchestration-LangChain%20LCEL-orange)
![Gemini](https://img.shields.io/badge/LLM-Gemini%202.5%20Flash-magenta)
![Security](https://img.shields.io/badge/Security-PII%20Guardrails-brightgreen)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit%20Dark-red)

> **[ 🇧🇷 Leia em Português ](README.pt-br.md)**

> **Executive Overview:** QualityOps is a production-grade GenAI compliance auditing and Site Reliability Engineering (SRE) platform built to automate quality assurance across 100% of customer support interactions in mission-critical field service operations, specifically for **Pest Control Operators (PCOs)**. The agent audits real-time calls for chemical safety protocols, service warranties, and regulatory compliance while enforcing deterministic pre-LLM PII sanitization, low-latency LangChain LCEL orchestration (<2s), and strict Pydantic v2 data contracts.

---

## 🏗️ 1. Platform Architecture & Data Flow

```mermaid
flowchart TD
    A[PCO Call Center Ingestion] --> B[1. Deterministic PII Guardrail]
    B -->|Sanitized Text + Violation Telemetry| C[2. Prompt Engine - LangChain LCEL]
    C -->|Zero-Temperature Low-Latency| D[3. Google Gemini 2.5 Flash]
    D -->|Raw JSON Output| E[4. Pydantic v2 Strict Contract Validation]
    E --> F[5. Real-Time Streamlit Executive Dashboard]
    E --> G[6. Automated Coaching & Feedback Dispatcher]
```

---

## 🛡️ 2. Enterprise Platform, Evals & Guardrails Standards

Designed following modern **GenAI Platform & LLMOps** requirements:

### 🏢 Real-World Domain: Pest Control Operator (PCO) Safety
* **Chemical Safety & Environmental Protocols:** Automatically evaluates whether operators provide mandatory safety disclaimers (e.g. pet/children isolation during spraying, minimum re-entry intervals, active ingredient transparency) to prevent regulatory fines and severe liability risks.
* **Warranty & Service Level Enforcement:** Verifies accurate explanation of re-treatment warranties, contract terms, and recurring visit scheduling.

### ⚡ Architectural Pivot: CrewAI → LangChain LCEL (<2s Latency)
* **Initial Bottleneck:** The initial prototype utilized a multi-agent CrewAI setup. Sequential agent debate and role-playing resulted in excessive latency (~15 seconds per call audit), making real-time supervisor intervention impossible.
* **Production Refactor:** Re-architected with **LangChain Expression Language (LCEL)** and **Gemini 2.5 Flash** at temperature `0.0`. Dropped end-to-end evaluation latency from 15s to **< 2.0 seconds** while slashing token consumption and ensuring deterministic outputs.

### 🔒 Deterministic Pre-LLM Guardrails (PII Protection)
* **Zero Trust Data Ingestion:** RegEx-based and heuristic pattern matchers intercept and mask Brazilian CPFs, credit card numbers, emails, and phone numbers before payloads reach external LLM endpoints.
* **Compliance Assurance:** Guarantees strict adherence to **LGPD**, **GDPR**, and **PCI-DSS** protocols.

### 🚨 Adversarial Resilience & Social Engineering Evals ("Michael Scott Attack")
* **Stress-Tested Against Coercion:** Evaluated against sophisticated social engineering prompts where callers invoke executive authority pressure ("I am the CEO, my system is locked, reset my credentials to my personal Gmail immediately!").
* **Deterministic Rejection:** The guardrail and prompt framework actively detect unauthorized administrative requests, flag the interaction as a critical security breach, and assign a score of **5/100**, instantly triggering supervisor alerts.

### 📐 Strict Data Contracts (Pydantic v2)
* Eliminates unvalidated dictionaries. All inputs and outputs conform strictly to `AuditRequest` and `AuditReport` models with automated type enforcement and score bounds (`0 <= score <= 100`).

### 📊 Streamlit Executive Dashboard & Automated Coaching
* Dark-mode executive interface providing real-time visibility into operator compliance scores, highlighted red flags, and automated, constructive coaching feedback generated for immediate agent improvement.

### 🧪 Automated Testing & CI Quality Gate
* Complete unit test suite (`pytest`) featuring deterministic mocks for API calls (0 token cost during CI).
* GitHub Actions automated quality pipeline executing linting (`ruff`) and test coverage verification on every commit.

---

## 📂 3. Repository Canonical Structure

```text
QualityOps-AI-Agent/
├── .github/
│   └── workflows/
│       └── ci.yml                     # Automated CI Quality Gate
├── src/
│   ├── models/
│   │   └── schemas.py                 # Pydantic v2 Strict Data Contracts
│   ├── guardrails/
│   │   └── pii_sanitizer.py           # Deterministic PII Interceptor
│   ├── langchain_backend.py           # LCEL Audit Pipeline & Gemini Engine
│   ├── app.py                         # Streamlit Executive Dashboard
│   └── main.py                        # Service Entrypoint
├── tests/
│   ├── conftest.py                    # Pytest Global Fixtures & LLM Mocks
│   └── unit/
│       ├── test_guardrails.py         # PII Masking & Security Tests
│       └── test_audit_engine.py       # Pydantic Contracts & Audit Tests
├── requirements.txt                   # Production Dependencies
└── README.md                          # Platform Technical Documentation
```

---

## 🚀 4. Quickstart & Local Execution

### Prerequisites
* Python 3.10+
* Google Gemini API Key

### Setup Environment
```bash
# 1. Clone repository
git clone https://github.com/jraphaelbarbosa/QualityOps-AI-Agent.git
cd QualityOps-AI-Agent

# 2. Setup virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
pip install pytest pytest-cov ruff
```

### Configure Credentials
Copy `.env.example` to `.env` and add your API key:
```bash
cp .env.example .env
# Edit .env and set GEMINI_API_KEY=your_key_here
```

### Run Unit Tests & CI Gate Locally
```bash
# Run tests with coverage
pytest --cov=src tests/

# Run linter
ruff check .
```

### Launch Streamlit Dashboard
```bash
streamlit run src/app.py
```
