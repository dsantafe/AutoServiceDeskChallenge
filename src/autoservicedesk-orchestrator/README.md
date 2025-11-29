# TechDesk Copilot – Multi-Agent Help Desk Orchestrator

A multi-agent help-desk system built on **Azure AI Agents**, **Azure DevOps MCP**, and a central orchestrator that evaluates user requests, applies policies, and triggers autonomous or assisted actions.

This project exposes a FastAPI endpoint that receives user requests and sends them through a complete decision and execution pipeline involving policy validation, user profile enrichment, DevOps operations, and UX-friendly responses.

---

## 📌 Features

### ✔ Multi-agent orchestration
- Central orchestrator defined in `orchestrator.py`
- Automatic request forwarding to the correct sub-agent
- Thread context management for conversations  
- Azure AI Agents used to run:
  - **Triage agent**
  - **MCP DevOps agent tools**
  - **Policy guard workflow**

### ✔ Policy Guard
- Validates roles, criticality, and internal rules
- Determines if a request:
  - is safe to auto-execute  
  - requires confirmation  
  - must be escalated  
  - should be rejected  
- Logic implemented in `policy.py` and `policy_guard_agent`

### ✔ Azure DevOps MCP Agent
Located at `agents/mcp_devops_agent.py`.

Supports MCP tools for:
- Creating repositories
- Restarting pipelines
- Assigning permissions
- Managing work items

### ✔ Knowledge Base Agent
Located at:
```
agents/knowledge_base_agent.py
```
Provides internal documentation answers via Azure AI Agents.

### ✔ Microsoft Teams / UX-Friendly Responses
Utility layer for:
- Confirmation interpretation  
- User-friendly summaries  
- Multi-agent run analysis  

Files involved:
```
agents_utils.py
run_utils.py
prompts/prompts.py
```

### ✔ User Profile Integration
`services/user_profile.py` enriches each request with:
- role  
- department  
- trust level  
- allowed operations  

This is used directly by the Orchestrator and Policy Guard.

### ✔ FastAPI Interface
`main.py` exposes:
- `POST /process` → Main endpoint
- `GET /health` → Health check

Runs locally with:
```bash
uvicorn main:app --reload --port 3000
```

---

## 🧩 Architecture Overview

```
           ┌────────────────────────────────┐
           │          FastAPI API           │
           └───────────────┬────────────────┘
                           │
                           ▼
              ┌──────────────────────────┐
              │      Orchestrator        │
              │   orchestrator.py        │
              └─────────────┬────────────┘
                            │
       ┌────────────────────┼─────────────────────┐
       ▼                    ▼                     ▼
┌──────────────┐     ┌──────────────┐     ┌────────────────┐
│ Policy Guard │     │ MCP DevOps   │     │ Knowledge Agent │
│ policy.py    │     │ mcp_devops_  │     │ knowledge_base_ │
│              │     │ agent.py     │     │ agent.py        │
└──────────────┘     └──────────────┘     └────────────────┘
                            │
                            ▼
                   Azure DevOps (MCP)
```

---

## 📂 Project Structure

```
help-desk-orchestrator/
│
├── main.py                     # FastAPI entrypoint
├── orchestrator.py             # Central multi-agent router
├── config.py                   # Azure config
├── context.py                  # Thread/session context handler
├── policy.py                   # Policy Guard logic
├── run_utils.py                # Multi-agent run analysis
├── agents_utils.py             # UX messages, confirmation logic
│
├── agents/
│   ├── policy_guard_agent.py
│   ├── mcp_devops_agent.py
│   └── knowledge_base_agent.py
│
├── services/
│   └── user_profile.py         # Dynamic user-role profile fetch
│
└── prompts/
    └── prompts.py              # System instructions for agents
```

---

## ⚙️ Installation

```bash
pip install -r requirements.txt
```

Environment variables required:

```
PROJECT_ENDPOINT=""
MODEL_DEPLOYMENT_NAME=""
MCP_SERVER_URL=""
POLICY_AGENT_ID=""
KNOWLEDGE_BASE_AGENT_ID=""
```

---

## ▶ Running the API

```bash
uvicorn main:app --reload --port 3000
```

Test with:

```bash
curl -X POST http://localhost:3000/process   -H "Content-Type: application/json"   -d '{
    "user_email": "someone@example.com",
    "message": "I need contributor access to repo X"
  }'
```

---

## 🔒 Policy Decision Flow

1. User request received  
2. User profile loaded  
3. Policy Guard checks:  
   - user role  
   - repository type  
   - action risk level  
4. Possible results:
   - `allow`  
   - `needs_confirmation`  
   - `escalate_to_human`  
   - `deny`  

---

## 🧠 Multi-Agent Execution Flow

1. Orchestrator creates agent instances  
2. Builds thread context  
3. Sends request to Triage Agent  
4. Routes to correct agent  
5. Analyzes run steps and returns final message  

---

## 🤝 Contribution

Contributions to:
- new MCP tools  
- improved routing  
- extended policy logic  
- richer knowledge prompts  
are welcome.

