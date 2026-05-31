# Implementation Plan: Production-Grade 10-Agent Enterprise Certification System (CertPrep-Ex)

This implementation plan outlines the architecture, data structures, agent roles, and execution plan for building a system that exceeds the previous hackathon winner's design.

---

## User Review Required

> [!IMPORTANT]
> **Key Architecture Decisions:**
> 1. **Targeting 3 Exams:** We will fully support **AI-102** (Azure AI Engineer), **AZ-204** (Azure Cloud Developer), and **AZ-400** (Azure DevOps Engineer). This aligns perfectly with the challenge rules, which require mapping certifications to organisational roles.
> 2. **10-Agent Collaborative Pipeline:**
>    - `LearnerProfilerAgent`: Structured profiles with a 3-tier LLM fallback.
>    - `LearningPathCuratorAgent`: Maps cert goals to MS Learn paths (Foundry IQ).
>    - `StudyPlanAgent`: Week-by-week schedule using a **Workload-Aware Largest Remainder Algorithm**.
>    - `EngagementAgent`: Personalizes study slot suggestions and reminders (Work IQ).
>    - `AssessmentAgent`: Generates domain-proportional quiz questions (Foundry IQ).
>    - `ProgressAgent`: Calculates weighted readiness scores based on exam-specific domain weights.
>    - `BookingRecommenderAgent`: Issues booking status (`GO` / `CONDITIONAL GO` / `NOT YET`).
>    - `ManagerInsightsAgent`: Aggregates team readiness, workload risks, and skill gaps (Fabric IQ + Work IQ).
>    - `PeerCollaborationAgent`: Recommends peer study buddy pairings.
>    - `QualityCriticAgent`: Run a 17-rule guardrail pipeline validation on agent boundaries.
> 3. **Engineering Highlights:**
>    - **3-Tier Fallback Chain:** Direct Azure AI Projects SDK -> OpenAI direct JSON-mode -> Rule-based offline engine.
>    - **Workload-Aware Largest Remainder:** Distributes study hours across domains using the Largest Remainder algorithm, adjusting dynamically for weeks where Work IQ signals show high meeting counts.
>    - **17-Rule Guardrail Pipeline:** Validates boundary inputs/outputs for formatting, PII, domain coverage, and grounding citations.
>    - **Streamlit Web UI:** Two distinct portals (Learner Space & Manager Dashboard) with real-time Plotly charts (Gantt, Domain radar, risk matrix) and an interactive **Agent Trace Console** showing reasoning traces.

---

## Open Questions

> [!NOTE]
> Please review these questions and provide your feedback in your chat response.
> 1. **Dual-Mode Execution:** To ensure the system runs in under 1 second and is 100% reliable for live demos, we will implement `FORCE_MOCK_MODE=True` as a default fallback toggle. Do you approve this approach?
> 2. **Test Suite:** Would you like us to create a comprehensive validation script representing a subset of the tests to verify the agent boundaries and fallback logic?

---

## Proposed Changes

We will build the project inside the workspace folder `c:/Users/adeto/Documents/Reazon`.

### 1. Data Layer

We will generate synthetic datasets for the three IQ intelligence layers.

#### [NEW] [synthetic data files](file:///c:/Users/adeto/Documents/Reazon/data)
- [learners.json](file:///c:/Users/adeto/Documents/Reazon/data/synthetic/learners.json): Synthetic profiles for 8 team members containing their current role, target exam, completed certifications, average study hours, and practice assessment scores.
- [work_signals.json](file:///c:/Users/adeto/Documents/Reazon/data/synthetic/work_signals.json): Synthetic Work IQ signals containing weekly meeting load, focus blocks, preferred learning windows, and weekly capacity.
- [certifications.json](file:///c:/Users/adeto/Documents/Reazon/data/synthetic/certifications.json): Fabric IQ Semantic ontology model mapping certifications (AI-102, AZ-204, AZ-400) to required skills, difficulty levels, prerequisite paths, and domain weights.
- [ai102_guide.md](file:///c:/Users/adeto/Documents/Reazon/data/documents/ai102_guide.md): Grounding guide for AI-102 (Azure OpenAI, AI Search, Document Intelligence).
- [az204_guide.md](file:///c:/Users/adeto/Documents/Reazon/data/documents/az204_guide.md): Grounding guide for AZ-204 (App Service, Azure Functions, Cosmos DB, API Management).
- [az400_guide.md](file:///c:/Users/adeto/Documents/Reazon/data/documents/az400_guide.md): Grounding guide for AZ-400 (CI/CD pipelines, Git branches, security scanning, container strategies).

---

### 2. Multi-Agent Engine (src/)

#### [NEW] [config.py](file:///c:/Users/adeto/Documents/Reazon/src/config.py)
Configuration settings, system constants, and schema models.

#### [NEW] [guardrails.py](file:///c:/Users/adeto/Documents/Reazon/src/guardrails.py)
A structured `GuardrailsPipeline` implementing 17 verification rules (e.g., PII check, citation presence, score bounds, domain match, schedule budget integrity).

#### [NEW] [scheduling.py](file:///c:/Users/adeto/Documents/Reazon/src/scheduling.py)
Implements the Largest Remainder algorithm for study hour distribution, integrated with Work IQ capacity constraints.

#### [NEW] [agents.py](file:///c:/Users/adeto/Documents/Reazon/src/agents.py)
Contains the class definitions for the 10 agents, each with dedicated system instructions, prompt models, and execution schemas.

#### [NEW] [main.py](file:///c:/Users/adeto/Documents/Reazon/src/main.py)
The primary entry point that coordinates agent interactions, runs the pipeline, records trace logs, and manages fallback behavior.

---

### 3. User Interface (ui/)

#### [NEW] [app.py](file:///c:/Users/adeto/Documents/Reazon/ui/app.py)
A clean, premium Streamlit dashboard with:
- **Learner Dashboard:** Gantt charts, radar charts, practice quizzes, and booking recommendations.
- **Manager Portal:** Aggregate analytics, team readiness risk heatmaps, and peer study buddy suggestions.
- **Agent Trace Console:** Interactive step-by-step logs showing the exact reasoning traces, fallback activations, and guardrail validations.

---

## Verification Plan

### Automated Verification
We will build a verification script `verify_system.py` that:
1. Tests the 3-tier LLM fallback chain.
2. Validates that the Largest Remainder scheduling algorithm correctly bounds hours.
3. Tests the 17-rule guardrail pipeline with intentionally bad input/output payloads.
4. Simulates a complete multi-agent pipeline run from Learner Profiler to Booking Recommendation.

### Manual Verification
1. Run `streamlit run ui/app.py` locally.
2. Verify visual rendering of Gantt and Radar charts.
3. Verify that changing a learner's meeting load in the UI triggers the workload adaptation.
4. Verify manager insights match aggregate statistics of the learners.
