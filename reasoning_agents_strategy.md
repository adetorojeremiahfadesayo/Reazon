# 🧠 Reasoning Agents Challenge — Strategy & Scenario Guide

This document presents **three concrete scenario options** for building the multi-agent enterprise learning system, ranked by complexity. Each scenario is designed to meet all submission requirements while targeting different levels of the evaluation rubric.

---

## Quick Comparison Matrix

| Dimension | 🟢 Scenario A: Practical MVP | 🟡 Scenario B: Ambitious Standard | 🔴 Scenario C: Maximum Impact |
|---|---|---|---|
| **Time to Build** | ~12–15 hours | ~18–25 hours | ~30–40 hours |
| **Development Approach** | Local (Agent Framework) | Hybrid (Local + Foundry SDK) | Full Cloud (Foundry + Hosted Agents) |
| **Number of Agents** | 3 core agents | 5 agents + orchestrator | 6 agents + orchestrator + evaluator |
| **IQ Layers** | Foundry IQ only | Foundry IQ + Fabric IQ | All three (Foundry + Fabric + Work IQ) |
| **Reasoning Pattern** | Planner–Executor | Planner–Executor + Critic | Planner–Executor + Critic + Self-Reflection |
| **Deployment** | Local CLI demo | Local + Foundry playground | Hosted Agent in Foundry Agent Service |
| **Estimated Score** | ~65–75% | ~78–88% | ~88–95% |

---

## 🟢 Scenario A: The Practical MVP

**Best for:** Getting a solid, working submission quickly with clean architecture and clear reasoning.

### Concept
Build a **3-agent local system** focused on the core learning flow: curate → plan → assess. Use Foundry IQ as your single IQ layer to ground all knowledge retrieval. Skip the engagement and manager agents — focus on depth over breadth.

### Architecture

```
┌──────────────────────────────────────────┐
│          Orchestrator (main.py)           │
│  Receives user input, routes to agents   │
└──────┬──────────┬──────────┬─────────────┘
       │          │          │
       ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────────┐
│ Learning │ │  Study   │ │  Assessment  │
│   Path   │ │   Plan   │ │    Agent     │
│ Curator  │ │Generator │ │              │
└──────────┘ └──────────┘ └──────────────┘
       │                         │
       ▼                         ▼
┌─────────────────────────────────────────┐
│         Foundry IQ Knowledge Base       │
│   (Synthetic docs, cert guides, FAQs)   │
└─────────────────────────────────────────┘
```

### Agent Responsibilities

| Agent | Role | Grounding | Tools |
|---|---|---|---|
| **Learning Path Curator** | Maps certification goals to skills & resources | Foundry IQ KB | Knowledge retrieval, Microsoft Learn MCP |
| **Study Plan Generator** | Creates time-boxed study schedule | Synthetic learner data (JSON) | Calendar logic, workload calculator |
| **Assessment Agent** | Generates cited practice questions & scores readiness | Foundry IQ KB | Question generation, scoring rubric |

### IQ Integration: Foundry IQ Only

1. **Create a Knowledge Base** in Azure AI Foundry with synthetic docs:
   - Engineering Certification Guide (markdown)
   - Quarterly Learning Report (markdown)
   - Certification skill mappings (JSON)
2. **Connect agents** to the KB via the Foundry SDK
3. **Require citations** — every recommendation or question must reference a source document

### Tech Stack
- **Framework:** Microsoft Agent Framework (local, OSS)
- **Language:** Python 3.10+
- **Model:** `gpt-4o` via Azure AI Foundry
- **Knowledge:** Azure AI Search + Foundry IQ
- **Interface:** CLI (terminal-based conversation)

### Reasoning Pattern: Planner–Executor
```
User Request
    │
    ▼
Orchestrator plans steps:
  1. "Identify certification target" → Learning Path Curator
  2. "Build study schedule" → Study Plan Generator  
  3. "Generate assessment" → Assessment Agent
    │
    ▼
Each agent executes its step and returns structured output
    │
    ▼
Orchestrator assembles final response
```

### Pros & Cons

| ✅ Pros | ❌ Cons |
|---|---|
| Fast to build (~12–15 hrs) | Missing engagement & manager agents |
| Clean, easy-to-demo architecture | Only 1 IQ layer (loses some points) |
| Strong reasoning with clear agent handoffs | No deployment story |
| Easy to debug and present | Less "wow factor" for creativity |

### Scoring Projection

| Criterion | Weight | Expected | Notes |
|---|---|---|---|
| Accuracy & Relevance | 25% | 18/25 | Meets core requirements, missing 2 agents |
| Reasoning & Multi-step | 25% | 20/25 | Clean planner-executor, clear handoffs |
| Creativity | 15% | 8/15 | Solid but not novel |
| UX & Presentation | 15% | 10/15 | CLI is functional but not polished |
| Reliability & Safety | 20% | 14/20 | Good data hygiene, basic guardrails |
| **Total** | | **~70/100** | |

---

## 🟡 Scenario B: The Ambitious Standard (⭐ Recommended)

**Best for:** Balancing completeness, creativity, and feasibility. Hits all submission requirements with room for extras.

### Concept
Build the **full 5-agent system** with an orchestrator, using a hybrid local + Foundry SDK approach. Integrate **Foundry IQ + Fabric IQ** as your two IQ layers. Add a Critic/Verifier pattern to the assessment flow. Include a simple Streamlit or Gradio web UI for demo polish.

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Web UI (Streamlit)                  │
│        Learner View  |  Manager Dashboard            │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│              Orchestrator Agent                       │
│  Routes requests, manages workflow state, handles    │
│  loops (fail → re-study → re-assess)                 │
└──┬────────┬────────┬────────┬────────┬──────────────┘
   │        │        │        │        │
   ▼        ▼        ▼        ▼        ▼
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐
│Learn │ │Study │ │Engage│ │Assess│ │ Manager  │
│Path  │ │Plan  │ │ment  │ │ment  │ │ Insights │
│Curat.│ │Gen.  │ │Agent │ │Agent │ │  Agent   │
└──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └────┬─────┘
   │        │        │        │           │
   ▼        ▼        ▼        ▼           ▼
┌──────────────┐ ┌────────┐ ┌─────────────────────┐
│  Foundry IQ  │ │Work IQ │ │     Fabric IQ       │
│  Knowledge   │ │Signals │ │   Semantic Layer     │
│    Base      │ │(Synth.)│ │  (Ontology Model)    │
└──────────────┘ └────────┘ └─────────────────────┘
```

### Agent Responsibilities

| Agent | Role | Grounding | Key Reasoning |
|---|---|---|---|
| **Orchestrator** | Routes workflow, manages state & loops | All agents | Decides next step based on agent outputs |
| **Learning Path Curator** | Maps cert goals → skills → resources | Foundry IQ | Retrieves cited content, ranks by relevance |
| **Study Plan Generator** | Creates capacity-aware study schedule | Fabric IQ semantic model | Models role→cert→skill relationships |
| **Engagement Agent** | Adapts reminders to work patterns | Synthetic Work IQ signals | Chooses timing based on focus windows |
| **Assessment Agent** | Generates grounded questions, scores readiness | Foundry IQ + Fabric IQ | Critic pattern: generates → validates → refines |
| **Manager Insights Agent** | Team-level progress & risk visibility | Fabric IQ analytics | Aggregates without exposing individual PII |

### IQ Integration Strategy

#### Foundry IQ (Knowledge Grounding)
```python
# Upload synthetic docs to Azure Blob Storage
# Create a Foundry IQ Knowledge Base pointing to those docs
# Connect Learning Path Curator + Assessment Agent to the KB

from azure.ai.projects import AIProjectClient

client = AIProjectClient(endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"])

# Agent queries KB and gets cited responses
response = client.agents.create_and_run(
    agent_id="learning-curator",
    instructions="Retrieve certification resources. Always cite sources.",
    tools=[{"type": "foundry_iq", "knowledge_base": "cert-kb"}]
)
```

#### Fabric IQ (Semantic Business Model)
```python
# Model the ontology as a structured JSON/Python layer
# This represents the "semantic model" that Fabric IQ would provide

SEMANTIC_MODEL = {
    "entities": {
        "Learner": {"attributes": ["id", "role", "team", "capacity_hours"]},
        "Certification": {"attributes": ["id", "skills", "pass_threshold", "recommended_hours"]},
        "Role": {"attributes": ["id", "primary_cert", "secondary_cert", "skill_gaps"]},
        "StudyPlan": {"attributes": ["learner_id", "cert_id", "milestones", "hours_allocated"]},
    },
    "relationships": [
        {"from": "Learner", "to": "Role", "type": "has_role"},
        {"from": "Role", "to": "Certification", "type": "requires"},
        {"from": "Certification", "to": "Skill", "type": "covers"},
        {"from": "Learner", "to": "StudyPlan", "type": "follows"},
    ],
    "rules": [
        "A learner needs ≥75% practice score before attempting certification",
        "Study hours should not exceed available focus hours per week",
        "Prerequisites must be completed before advanced certifications",
    ]
}
```

### Reasoning Patterns

#### Pattern 1: Planner–Executor (Orchestrator)
The orchestrator decomposes the user request into a multi-step plan and dispatches to agents sequentially.

#### Pattern 2: Critic/Verifier (Assessment Agent)
```
Assessment Agent generates questions
    │
    ▼
Critic sub-step: "Are these questions grounded in the KB? Are citations valid?"
    │
    ├── YES → Return questions to learner
    └── NO  → Regenerate with stricter grounding constraints
```

#### Pattern 3: Feedback Loop (Orchestrator)
```
Assessment result < 75%
    │
    ▼
Orchestrator loops back:
  → Study Plan Generator: "Add 5 more hours on weak topics"
  → Engagement Agent: "Increase check-in frequency"
  → Assessment Agent: "Re-assess in 1 week"
```

### Web UI (Streamlit)

Two views for maximum demo impact:

**Learner View:**
- Chat interface to interact with the system
- Visual study plan (timeline/calendar)
- Practice assessment with cited questions
- Progress tracker with readiness score

**Manager Dashboard:**
- Team overview with per-learner status
- Risk heatmap (who's at risk of failing?)
- Capacity analysis (who's overloaded?)
- Completion trend charts

### Tech Stack
- **Framework:** Microsoft Agent Framework (local) + Foundry SDK
- **Language:** Python 3.10+
- **Model:** `gpt-4o` via Azure AI Foundry
- **Knowledge:** Foundry IQ (Azure AI Search + Blob Storage)
- **Semantic Layer:** Fabric IQ modelled as Python ontology + synthetic data
- **Work Signals:** Synthetic Work IQ data (JSON)
- **UI:** Streamlit or Gradio
- **MCP:** Microsoft Learn MCP server for supplementary content
- **Monitoring:** Azure AI Foundry tracing + custom logging

### Implementation Phases

| Phase | Duration | Deliverable |
|---|---|---|
| 1. Setup & Data | ~3 hours | Repo, venv, Azure project, synthetic data, Foundry IQ KB |
| 2. Core Agents | ~8 hours | 5 agents + orchestrator with basic routing |
| 3. IQ Integration | ~4 hours | Foundry IQ retrieval + Fabric IQ semantic model |
| 4. Reasoning Patterns | ~3 hours | Critic pattern, feedback loops, multi-step planning |
| 5. Web UI | ~4 hours | Streamlit learner + manager views |
| 6. Polish & Docs | ~3 hours | README, demo script, evaluation, responsible AI |
| **Total** | **~25 hours** | |

### Scoring Projection

| Criterion | Weight | Expected | Notes |
|---|---|---|---|
| Accuracy & Relevance | 25% | 22/25 | All 5 agents, 2 IQ layers, meets all requirements |
| Reasoning & Multi-step | 25% | 22/25 | Planner + Critic + Feedback loops |
| Creativity | 15% | 12/15 | Dual UI views, semantic ontology, MCP integration |
| UX & Presentation | 15% | 13/15 | Polished Streamlit with charts and visuals |
| Reliability & Safety | 20% | 16/20 | Guardrails, synthetic data, tracing |
| **Total** | | **~85/100** | |

---

## 🔴 Scenario C: Maximum Impact

**Best for:** Going all-in for a top placement. Full architecture, all three IQ layers, hosted deployment, evaluations, and advanced reasoning.

### Concept
Build the **complete 6-agent system** with a sophisticated orchestrator, deploy as **Hosted Agents in Foundry Agent Service**, integrate **all three IQ layers**, implement **advanced reasoning patterns** (self-reflection, chain-of-thought, critic), add **evaluation pipelines**, and deliver a **polished React web app** with real-time agent trace visualization.

### Architecture

```
┌──────────────────────────────────────────────────────────┐
│                  React Web Application                    │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │  Learner   │  │   Manager    │  │  Agent Trace     │ │
│  │  Portal    │  │  Dashboard   │  │  Visualizer      │ │
│  └────────────┘  └──────────────┘  └──────────────────┘ │
└───────────────────────┬──────────────────────────────────┘
                        │ REST API
┌───────────────────────▼──────────────────────────────────┐
│           FastAPI Backend + WebSocket Events              │
└───────────────────────┬──────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────┐
│        🧠 Meta-Orchestrator (Hosted Agent)                │
│   ┌─────────────────────────────────────────────────┐    │
│   │  1. Parse intent (learner vs manager request)   │    │
│   │  2. Decompose into agent plan                   │    │
│   │  3. Execute plan with state tracking            │    │
│   │  4. Self-reflect: "Is this response complete?"  │    │
│   │  5. If not → refine and re-execute              │    │
│   └─────────────────────────────────────────────────┘    │
└──┬──────┬──────┬──────┬──────┬──────┬────────────────────┘
   │      │      │      │      │      │
   ▼      ▼      ▼      ▼      ▼      ▼
┌─────┐┌─────┐┌─────┐┌─────┐┌─────┐┌──────────┐
│Curat││Plan ││Engag││Asses││Manag││Evaluation│
│or   ││Gen  ││ment ││ment ││er   ││  Agent   │
│Agent││Agent││Agent││Agent││Agent││ (Critic) │
└──┬──┘└──┬──┘└──┬──┘└──┬──┘└──┬──┘└────┬─────┘
   │      │      │      │      │         │
   ▼      ▼      ▼      ▼      ▼         ▼
┌──────────────────────────────────────────────────────────┐
│                    IQ Integration Layer                    │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐ │
│  │  Foundry IQ  │ │  Fabric IQ   │ │     Work IQ      │ │
│  │  Knowledge   │ │  Semantic    │ │  Work Context    │ │
│  │  Grounding   │ │  Ontology    │ │  Signals         │ │
│  └──────────────┘ └──────────────┘ └──────────────────┘ │
└──────────────────────────────────────────────────────────┘
         │                  │                  │
         ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│ Azure Blob + │  │  Semantic    │  │  Synthetic M365  │
│ AI Search    │  │  Model DB    │  │  Activity Data   │
│ (Synth Docs) │  │  (Ontology)  │  │  (JSON/API)      │
└──────────────┘  └──────────────┘  └──────────────────┘
```

### Advanced Reasoning Patterns

#### 1. Self-Reflection (Meta-Orchestrator)
```
Orchestrator produces a plan
    │
    ▼
Self-check: "Does this plan cover all the user's needs?"
    │
    ├── Confidence HIGH → Execute
    └── Confidence LOW → Decompose further, add clarifying questions
```

#### 2. Chain-of-Thought with Trace Logging
Each agent emits reasoning traces that are:
- Logged for observability
- Displayed in the UI's "Agent Trace Visualizer"
- Used by the Evaluation Agent to audit quality

```python
# Every agent response includes structured reasoning
{
    "agent": "assessment_agent",
    "reasoning_trace": [
        "Step 1: Retrieved 12 documents from Foundry IQ KB for AZ-204",
        "Step 2: Filtered to 5 documents covering 'Azure Functions' skill area",
        "Step 3: Generated 3 practice questions with citations",
        "Step 4: Critic check — all citations verified against KB",
        "Step 5: Confidence: 0.92 — returning questions"
    ],
    "output": { ... },
    "citations": [ ... ]
}
```

#### 3. Critic / Evaluation Agent
A dedicated 6th agent that:
- Reviews outputs from other agents for quality and grounding
- Flags hallucinated or uncited content
- Assigns confidence scores
- Triggers re-generation when quality is below threshold

#### 4. Adaptive Feedback Loops
```
Assessment < 75%
    │
    ▼
Evaluation Agent analyses failure patterns:
  "Learner weak in Azure Functions (2/5 correct)"
    │
    ▼
Study Plan Generator: "Add targeted Azure Functions module"
    │
    ▼
Engagement Agent: "Schedule extra sessions during Thursday focus block"
    │
    ▼
Re-assess in next cycle with targeted questions
```

### All Three IQ Layers

| IQ Layer | Implementation | Used By |
|---|---|---|
| **Foundry IQ** | Azure AI Search KB with synthetic docs uploaded to Blob Storage. Agents query via Foundry SDK with citation requirements. | Curator, Assessment |
| **Fabric IQ** | Python-based semantic ontology modelling entities (Learner, Role, Certification, Skill, StudyPlan) with relationships and business rules. Backed by SQLite or JSON for the demo. | Plan Generator, Assessment, Manager Insights |
| **Work IQ** | Synthetic work activity API (FastAPI microservice) serving meeting hours, focus windows, collaboration patterns per employee. Simulates M365 Graph signals. | Engagement Agent, Plan Generator |

### Hosted Agent Deployment

```
┌─────────────────────────────────────────────┐
│        Azure Container Registry              │
│   ┌───────────────────────────────────┐     │
│   │  reasoning-agents:v1.0            │     │
│   │  (Docker image with all agents)   │     │
│   └───────────────────────────────────┘     │
└───────────────────┬─────────────────────────┘
                    │
┌───────────────────▼─────────────────────────┐
│      Foundry Agent Service (Hosted)          │
│   • Managed compute                          │
│   • Entra ID agent identity                  │
│   • Session state persistence                │
│   • Auto-scaling                             │
│   • Telemetry & tracing                      │
└───────────────────┬─────────────────────────┘
                    │
                    ▼
              Agent Endpoint
         (accessible via REST API)
```

### Evaluation Pipeline

```python
# Automated evaluation using Foundry SDK
from azure.ai.evaluation import evaluate

results = evaluate(
    data="test_cases.jsonl",
    evaluators={
        "groundedness": GroundednessEvaluator(),
        "relevance": RelevanceEvaluator(),
        "citation_accuracy": CitationEvaluator(),
        "safety": SafetyEvaluator(),
    },
    target=agent_pipeline,
)
```

### Scoring Projection

| Criterion | Weight | Expected | Notes |
|---|---|---|---|
| Accuracy & Relevance | 25% | 24/25 | Complete system, all IQ layers, all agents |
| Reasoning & Multi-step | 25% | 24/25 | Self-reflection + Critic + Adaptive loops + CoT |
| Creativity | 15% | 14/15 | Agent trace viz, evaluation pipeline, Work IQ API |
| UX & Presentation | 15% | 14/15 | React app, real-time traces, manager dashboard |
| Reliability & Safety | 20% | 18/20 | Evaluations, guardrails, hosted deployment, Responsible AI |
| **Total** | | **~94/100** | |

---

## 🎯 Decision Framework: Which Scenario to Choose?

```
START
  │
  ├── Do you have < 15 hours?
  │     └── YES → 🟢 Scenario A (Practical MVP)
  │
  ├── Do you have 15–25 hours?
  │     └── YES → 🟡 Scenario B (Ambitious Standard) ⭐ RECOMMENDED
  │
  ├── Do you have 25+ hours AND Azure pay-as-you-go?
  │     └── YES → 🔴 Scenario C (Maximum Impact)
  │
  └── Are you on Azure Free Tier with tight quotas?
        └── YES → 🟢 Scenario A or 🟡 Scenario B (local-first approach)
```

---

## 📁 Recommended Project Structure (All Scenarios)

```
reasoning-agents/
├── README.md                          # Project overview & demo instructions
├── .gitignore                         # .env, .venv/, __pycache__/
├── .env.example                       # Template for environment variables
├── requirements.txt                   # Python dependencies
├── pyproject.toml                     # Project metadata
│
├── data/                              # All synthetic data
│   ├── synthetic/
│   │   ├── learners.json              # Learner performance records
│   │   ├── work_signals.json          # Work activity signals
│   │   ├── certifications.json        # Certification definitions
│   │   └── teams.json                 # Team compositions
│   └── documents/                     # Synthetic knowledge docs
│       ├── cert_guide.md              # Engineering Certification Guide
│       ├── learning_report.md         # Team Learning Report
│       ├── workload_insights.md       # Workload Insights Report
│       └── study_patterns.md          # Study Pattern Analysis
│
├── src/
│   ├── __init__.py
│   ├── main.py                        # Entry point
│   ├── config.py                      # Environment & configuration
│   │
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── planner.py                 # Decomposes requests into agent plans
│   │   └── router.py                  # Routes tasks to appropriate agents
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py              # Abstract base with common logic
│   │   ├── learning_curator.py        # Learning Path Curator
│   │   ├── study_planner.py           # Study Plan Generator
│   │   ├── engagement.py              # Engagement Agent
│   │   ├── assessment.py              # Assessment Agent
│   │   ├── manager_insights.py        # Manager Insights Agent
│   │   └── evaluation.py             # Critic/Evaluation Agent (Scenario C)
│   │
│   ├── iq_layers/
│   │   ├── __init__.py
│   │   ├── foundry_iq.py              # Knowledge base retrieval
│   │   ├── fabric_iq.py               # Semantic ontology model
│   │   └── work_iq.py                 # Work context signals
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── calendar_tool.py           # Study scheduling tool
│   │   ├── search_tool.py             # Knowledge search tool
│   │   └── mcp_client.py             # Microsoft Learn MCP client
│   │
│   └── models/
│       ├── __init__.py
│       ├── learner.py                 # Learner data model
│       ├── certification.py           # Certification data model
│       └── study_plan.py              # Study plan data model
│
├── ui/                                # Web UI (Scenario B & C)
│   ├── app.py                         # Streamlit app (Scenario B)
│   └── frontend/                      # React app (Scenario C)
│
├── evaluation/                        # Evaluation pipeline
│   ├── test_cases.jsonl               # Test scenarios
│   ├── evaluate.py                    # Evaluation runner
│   └── rubrics.json                   # Scoring rubrics
│
├── deployment/                        # Hosted agent deployment (Scenario C)
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── deploy.sh
│
└── docs/
    ├── architecture.md                # Architecture documentation
    ├── agent_responsibilities.md      # Agent role descriptions
    ├── data_dictionary.md             # Synthetic data documentation
    └── responsible_ai.md              # Responsible AI documentation
```

---

## 🚀 Recommended First Steps (Regardless of Scenario)

### Step 1: Environment Setup (~1 hour)
```bash
# Create project
mkdir reasoning-agents && cd reasoning-agents
git init

# Python environment
python -m venv .venv
.venv\Scripts\activate

# Install core dependencies
pip install azure-ai-projects azure-identity python-dotenv

# Set up Azure
# → Go to https://ai.azure.com
# → Create a Foundry project
# → Deploy gpt-4o model
# → Copy project endpoint to .env
```

### Step 2: Synthetic Data (~1 hour)
Create rich, realistic-but-fictional datasets that demonstrate your system's capabilities. Expand beyond the starter kit examples with:
- 10+ learners across 3+ teams
- 5+ certifications with skill mappings
- Work signals for each employee
- Historical study outcomes

### Step 3: First Agent (~2 hours)
Start with the **Learning Path Curator** — it's the entry point to the system and lets you validate your Foundry IQ knowledge base integration immediately.

### Step 4: Orchestrator (~2 hours)
Build the routing logic that connects agents into a workflow. Start simple (sequential) then add conditional logic and loops.

### Step 5: Iterate
Add agents one at a time, test the end-to-end flow after each addition.

---

## ⚠️ Key Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Azure free tier quota limits | Start local with Agent Framework; only deploy to Foundry for final testing |
| Foundry IQ setup complexity | Start with a simple 2–3 doc KB; expand later |
| Time overrun on UI | Use Streamlit (fast) over React (polished but slow) |
| Agent responses are generic | Tighten system prompts, require structured JSON output, add grounding constraints |
| MCP server integration issues | MCP is a "nice to have" — integrate last, skip if blocked |
| Hosted Agent deployment fails | Keep local demo as fallback; document the deployment *intent* |

---

## 💡 Differentiator Ideas (For Standing Out)

1. **Agent Trace Visualizer** — Show the user exactly how agents reasoned, with expandable thought chains
2. **Adaptive Difficulty** — Assessment Agent adjusts question difficulty based on past performance
3. **Team Risk Heatmap** — Manager sees a visual grid of team readiness with color-coded risk levels
4. **Study Buddy Matching** — Match learners studying the same certification for peer support
5. **Certification Pathway Graph** — Interactive graph showing prerequisite chains and recommended order
6. **Confidence Calibration** — Agents report confidence levels; low-confidence answers get flagged for human review
7. **Microsoft Learn MCP Integration** — Pull real learning paths and module descriptions via MCP
8. **Multi-language Support** — Engagement Agent sends reminders in the learner's preferred language

---

> [!IMPORTANT]
> **My recommendation: Start with Scenario B.** It hits all the submission requirements, scores well across every evaluation criterion, and is achievable in a focused weekend of work. You can always scale up to Scenario C elements (hosted deployment, Work IQ, evaluation pipeline) if time permits.
