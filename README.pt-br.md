# QualityOps AI — Auditor de Conformidade & Guardrails Enterprise

[![CI Quality Gate](https://github.com/jraphaelcunha/qualityops-ai-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/jraphaelcunha/qualityops-ai-agent)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Pydantic v2](https://img.shields.io/badge/Contracts-Pydantic%20v2-red)
![Licença: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![LangChain](https://img.shields.io/badge/LangChain-LCEL-orange)
![Gemini](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-magenta)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red)

> **[ Read in English ](README.md)**

O **QualityOps** é um auditor autônomo de conformidade e confiabilidade (SRE) desenhado para operações de suporte e serviços de campo (**Pest Control Operators - PCO**). O sistema audita transcrições de atendimento verificando protocolos de segurança química, garantias contratuais, prevenção contra vazamento de PII e tentativas de engenharia social com latência inferior a `2.0s`.

Para detalhes sobre o pivot arquitetural (`~15s` → `<2.0s`) e decisões de segurança, consulte [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

> **Governança de Propriedade Intelectual (NDA, LGPD & PCI-DSS):** Este repositório público é uma arquitetura de referência sanitizada. Políticas proprietárias de clientes, gravações reais e credenciais de produção permanecem estritamente confidenciais sob NDA; todas as transcrições em `data/mock_chat_logs.json` e `eval/dataset/compliance_v1.jsonl` são fixtures sintéticas.

---

## Principais Recursos & Decisões de Arquitetura

* **Domínio Crítico (Serviços de Campo / PCO):** Verifica se operadores fornecem instruções obrigatórias de segurança química (isolamento de pets/crianças, intervalo mínimo de reentrada) e termos de garantia contratual.
* **Pivot Arquitetural: CrewAI (`~15s`) → LangChain LCEL (`<2.0s`):** A migração de múltiplos agentes sequenciais no CrewAI para passagem única declarativa em **LangChain LCEL + Gemini 2.5 Flash (`temperature=0.0`)**, somada à extração de PII/riscos para Python puro (`<5ms`), reduziu a latência ponta a ponta para menos de 2 segundos.
* **Interceptação Determinística de PII & Safety Overrides:** `src/guardrails/pii_sanitizer.py` mascara CPFs, cartões de crédito, e-mails, telefones e chaves de API via RegEx antes da chamada à LLM. Vazamentos críticos ou riscos químicos acionam bloqueio determinístico (`score <= 30`, `security_violation=True`) e fila de revisão humana (`HITLTrigger`).
* **Contratos Rígidos em Pydantic v2:** `AuditRequest` e `AuditReport` com validação estrita (`extra="forbid"`), limites de pontuação e telemetria `latency_ms`.

---

## Instalação e Execução

```bash
git clone https://github.com/jraphaelcunha/qualityops-ai-agent.git
cd qualityops-ai-agent

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
pip install -r requirements-dev.txt

cp .env.example .env
# Edite .env e configure: GEMINI_API_KEY="your_gemini_api_key_here"

streamlit run src/app.py
```

## Testes, Segurança e Avaliação

```bash
ruff check src/ tests/ eval/
bandit -r src/
pytest tests/ -v --cov=src --cov-report=term-missing
python eval/evaluate.py --dataset eval/dataset/compliance_v1.jsonl --mock
```

---

**Autor:** João Raphael Cunha | Distribuído sob licença [MIT](LICENSE).
