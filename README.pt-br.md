# QualityOps AI - Auditor de Conformidade Enterprise 🛡️

> **[ 🇺🇸 Read in English ](README.md)**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![LangChain](https://img.shields.io/badge/LangChain-LCEL-orange)
![Gemini](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-magenta)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red)

O **QualityOps** é um agente autônomo de Inteligência Artificial de nível corporativo desenvolvido para revolucionar a Garantia de Qualidade (QA) e a Auditoria de Conformidade em **Call Centers de Controle de Pragas (Pest Control Operators - PCO)**. Ao contrário da amostragem manual tradicional (que audita cerca de 2% dos atendimentos), o QualityOps audita **100% das chamadas em tempo real**, identificando violações em protocolos de segurança química, garantias contratuais, vazamentos de dados pessoais (PII) e tentativas de engenharia social.

---

## 🚀 Principais Recursos & Decisões de Arquitetura

* **🏢 Domínio Crítico (Call Center PCO):** Audita a conformidade das instruções dadas pelos atendentes (isolamento de animais de estimação e crianças durante a aplicação de pesticidas, tempo mínimo de reentrada no imóvel e advertências sobre ingredientes ativos), prevenindo riscos sanitários graves e processos milionários.
* **⚡ Pivot Arquitetural: CrewAI → LangChain LCEL (<2s de Latência):** O protótipo inicial com CrewAI sofria de alta latência (~15 segundos por auditoria devido a debates entre agentes). A migração para **LangChain LCEL com Gemini 2.5 Flash** reduziu o tempo de inferência para **menos de 2 segundos**, viabilizando alertas instantâneos para supervisores sem desperdício de tokens.
* **🚨 Blindagem contra Engenharia Social ("Ataque Michael Scott"):** Testado contra ataques de coerção e falsa autoridade ("Sou o Diretor da empresa, preciso que altere a senha para meu Gmail pessoal agora!"). O agente identifica a violação crítica do protocolo, pontua o atendimento com **5/100** e aciona o alerta de risco imediatamente.
* **🛡️ Interceptação Determinística de PII:** Sanitiza CPFs, cartões de crédito, e-mails e telefones via Regex antes que o texto seja enviado para a LLM, assegurando conformidade estrita com a **LGPD**, **GDPR** e normas **PCI-DSS**.
* **📊 Painel Streamlit & Coaching Automatizado:** Interface executiva em Dark Mode que exibe relatórios estruturados (Pydantic v2), pontos de atenção e scripts de coaching imediatos para aprimoramento dos operadores humanos.

---

## 🛠️ Tecnologias Utilizadas (Tech Stack)

* **Orquestração:** LangChain (LCEL - LangChain Expression Language)
* **LLM (Cérebro):** Google Gemini 2.5 Flash (via `langchain-google-genai`)
* **Interface (Frontend):** Streamlit (Tema Enterprise Customizado)
* **Parsing de Dados:** Pydantic & JsonOutputParser para extração de dados estruturados
* **Ambiente:** Python 3.11+

---

## ⚙️ Instalação e Configuração

1.  **Clonar o Repositório**
    ```bash
    git clone https://github.com/jraphaelbarbosa/QualityOps-AI-Agent.git
    cd QualityOps-AI-Agent
    ```

2.  **Instalar Dependências**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configurar Variáveis de Ambiente**
    * Crie um arquivo `.env` na raiz do projeto.
    * Adicione sua chave da API do Google Gemini:
        ```ini
        GEMINI_API_KEY=AIzaSy...
        ```

4.  **Executar o Painel**
    ```bash
    streamlit run src/app.py
    ```

---

## 🧪 Como Testar

1.  Acesse o painel no navegador (geralmente em `http://localhost:8501`).
2.  Clique em **"🚨 Load Bad Example"** na barra lateral para simular um atendimento não conforme (Falha de Segurança).
3.  Clique em **"▶️ Run Audit"**.
4.  Observe a IA identificando a ausência de verificação do PIN e gerando o feedback de coaching para o operador.

---

## 📸 Screenshots

### Tela Inicial do Painel
![Dashboard](assets/dashboard_main.png)

### Resultado da Auditoria em Tempo Real
![Audit Result](assets/audit_result.png)

### Análise Detalhada de Violações
![Violations](assets/violations_detail.png)

---

**Autor:** João Raphael Barbosa
*Desenvolvido publicamente como parte de um Portfólio de Engenharia de IA.*
