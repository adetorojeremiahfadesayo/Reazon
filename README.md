# Reazon Internship Development Program

A 10-agent internship development and Microsoft certification readiness system for startup teams. It helps companies onboard interns into role-aligned technical tracks, generate workload-aware study plans, take cited final assessments, unlock synthetic badges, and give program managers aggregate readiness visibility.

This project is built for the Reasoning Agents track and uses synthetic data only.

## What It Does

- Profiles interns from role and exam goals.
- Supports 18 Microsoft certification tracks across Azure, AI, data, security, Microsoft 365, Dynamics, Power Platform, DevOps, and architecture.
- Curates certification-specific Microsoft Learn-style course paths using a local registry and cited markdown guides.
- Generates week-by-week study plans with workload-aware Largest Remainder allocation.
- Creates grounded final exam questions with citations.
- Verifies learning activity from Microsoft Learn/LMS/Teams-style evidence.
- Calculates WorkIQ-aware intern readiness and returns `GO`, `CONDITIONAL GO`, or `NOT YET`.
- Unlocks a synthetic badge when the final exam score is at least 65%.
- Persists traces and badges in SQLite.
- Exposes both Streamlit and FastAPI surfaces.

## Internship Story

The demo can be presented as a company internship program: a startup hires interns across cloud, AI, data, security, operations, and business application roles, then uses Reazon to assign each intern a Microsoft-aligned development track. Reazon turns the intern's role and target track into a study plan, monitors learning evidence, runs a final readiness assessment, and gives managers a simple view of who is ready, who needs remediation, and which PDFs document progress.

## Course Specificity

The courses are not random general courses. Reazon maps each intern to a specific Microsoft certification target, such as `AZ-204`, `AI-900`, or `SC-900`, then uses that exam's weighted domains to build the course path. The current demo links to Microsoft Learn certification/search surfaces and cites local guide files in `data/documents`; in production, those links can be replaced with exact company LMS course IDs or Microsoft Learn module assignments.

## Agent Architecture

1. `LearnerProfilerAgent` builds structured learner profiles.
2. `LearningPathCuratorAgent` maps exam domains to Microsoft Learn resources.
3. `StudyPlanAgent` creates workload-aware schedules.
4. `EngagementAgent` recommends study windows.
5. `AssessmentAgent` generates cited exam questions.
6. `ProgressAgent` computes Reazon readiness scores using exam mastery, assessment score, study momentum, and workload fit.
7. `BookingRecommenderAgent` issues booking guidance.
8. `LearningActivityVerifierAgent` validates whether planned learning actually happened.
9. `ManagerInsightsAgent` aggregates team readiness and risk.
10. `PeerCollaborationAgent` recommends study buddies.
11. `QualityCriticAgent` validates inputs, outputs, citations, scores, privacy, badge rules, workload signals, and manager penalty policy.

## Readiness Logic

Each learner is measured against their own Microsoft exam target. The certification ontology supplies that exam's domains and weights, then Reazon applies this formula:

```text
Readiness = 0.45 * exam-domain mastery
          + 0.25 * latest assessment score
          + 0.15 * study-hours utilization
          + 0.15 * WorkIQ workload fit
```

This keeps the product exam-pack focused while making it different from a generic cert-prep clone: a learner with strong quiz scores but a meeting-heavy calendar can still receive a lower readiness confidence because the system predicts less capacity to finish the plan.

## Microsoft IQ Layers

Demo mode uses synthetic local equivalents:

- **Foundry IQ:** local markdown course guides in `data/documents`.
- **Fabric IQ:** certification ontology in `data/synthetic/certifications.json`.
- **Work IQ:** synthetic meeting, focus, and study-budget signals in `data/synthetic/work_signals.json`.
- **Microsoft Graph connector:** live-ready connector with synthetic Graph calendar/class-attendance demo data.
- **LMS connector:** Moodle-style connector with synthetic completion/checkpoint demo data.

Production mode would replace these with Azure AI Foundry knowledge bases, Fabric-backed semantic data, and consented Microsoft Graph/M365 work signals.

## Live-Ready Connectors

The repository includes deployment-ready connector scaffolds that default to synthetic data:

- `MicrosoftGraphConnector`: reads synthetic Graph-style meeting/class attendance by default, or can call Microsoft Graph with app-only OAuth when `GRAPH_USE_LIVE=true`.
- `MoodleLmsConnector`: chosen LMS adapter for course completion/checkpoint signals. It defaults to synthetic Moodle-style data and can be swapped for another LMS later.
- Azure AI Foundry profile generation: Tier 1 in the 3-tier fallback chain uses `AIProjectClient` and `DefaultAzureCredential` when `FORCE_MOCK_MODE=false`.

Do not commit real secrets. Use `.env`, managed identity, or Azure Key Vault.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Run the Streamlit app:

```powershell
streamlit run ui/app.py
```

Run the FastAPI backend:

```powershell
.\.venv\Scripts\python.exe -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

Run the React web app:

```powershell
cd web
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

Open API docs:

```text
http://127.0.0.1:8000/docs
```

One-command demo launcher for Windows:

```powershell
.\scripts\start_demo.ps1
```

If the web app shows `Request failed with 500` on first load, confirm the API is running:

```powershell
curl.exe http://127.0.0.1:8000/health
curl.exe http://127.0.0.1:8000/api/learners
```

Both commands should return JSON. If they do not, start the backend with the virtualenv command above.

Run verification:

```powershell
python verify_system.py
pytest -q
```

Run the web automation test at 1.5x UI motion:

```powershell
cd web
npm run test:e2e
```

The E2E test starts FastAPI and Vite, opens `/?testSpeed=1.5`, verifies the learner workspace, runs the pipeline, fills the demo passing answers, submits the assessment, and checks the tiered badge result.

## API Endpoints

- `GET /health`
- `GET /api/learners`
- `GET /api/reports`
- `POST /api/learner/profile`
- `POST /api/learner/plan`
- `POST /api/learner/assessment`
- `POST /api/learner/assessment/submit`
- `POST /api/learner/activity`
- `POST /api/manager/insights`

## Reports

The backend can export PDFs for:

- Study plans
- Readiness reports
- Badge certificates

PDFs are written to `data/reports`.

## Demo Mode

`FORCE_MOCK_MODE=True` is set by default for reliable live demos with no credentials. The pipeline runs using deterministic local data and validates the same typed contracts used by production integrations.

## 3-Tier LLM Fallback Chain

The learner profiler supports a real three-tier fallback path:

1. **Tier 1: Azure AI Foundry project client**
   Uses `AZURE_AI_PROJECT_ENDPOINT`, `AZURE_AI_MODEL_DEPLOYMENT`, and `DefaultAzureCredential` to create an Azure OpenAI-compatible client from the Foundry project.

2. **Tier 2: Direct Azure OpenAI JSON mode**
   Uses `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_API_VERSION`, and `AZURE_AI_MODEL_DEPLOYMENT`.

3. **Tier 3: deterministic local parser**
   Uses synthetic learner data and rule-based parsing. This is the default demo path when `FORCE_MOCK_MODE=true` or cloud credentials are unavailable.

Copy `.env.example` to `.env` and set `FORCE_MOCK_MODE=false` to attempt the Azure tiers.

## Responsible AI and Data Safety

All learner records, work signals, course guides, and certification scenarios are synthetic. The content is not official Microsoft exam material and is not an exam dump. Learners should verify real certification objectives through Microsoft Learn before booking a real exam.

Do not commit `.env`, API keys, tenant data, customer data, real employee data, or confidential content.

## Production Path

1. Replace local markdown search with Foundry IQ.
2. Replace JSON ontology with Fabric-backed semantic storage.
3. Replace synthetic Work IQ with Microsoft Graph/M365 signals under tenant consent.
4. Add Entra ID auth and manager role checks to FastAPI.
5. Deploy the Docker image to Azure Container Apps, App Service, or Foundry Hosted Agents.
6. Import the FastAPI OpenAPI schema into Copilot Studio as custom actions.
