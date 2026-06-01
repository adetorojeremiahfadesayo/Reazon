# Demo Script

## 1. Opening

This is Reazon: Microsoft Certification Readiness, a 10-agent workforce development platform for startup teams preparing workers and interns for Microsoft exams.

The system uses synthetic data only and demonstrates Foundry IQ, Fabric IQ, and Work IQ concepts locally for reliable demo execution.

## 2. Learning Demo

1. Run `streamlit run ui/app.py`.
2. Open the Learning Space.
3. Select a worker or intern persona.
4. Click **Execute Collaborative Agent Pipeline**.
5. Show:
   - learner profile
   - Work IQ meeting and study budget signals
   - workload-aware Gantt schedule
   - curated Microsoft Learn resources and citations
   - engagement recommendation
   - agent traces

## 3. Final Exam and Badge Demo

1. Answer the final exam questions.
2. Submit the final exam.
3. Explain that 65% unlocks a synthetic workforce professional badge.
4. Show the badge card and persistent badge count.
5. Explain that the badge is not an official Microsoft credential.

## 4. Manager Dashboard

1. Switch to Manager Insights Portal.
2. Show:
   - total learners
   - average readiness
   - workload burnout risks
   - unlocked badges
   - readiness by certification
   - peer study pairs
   - manager agent traces

## 5. API Demo

Run:

```powershell
uvicorn api.main:app --reload --port 8000
```

Open:

```text
http://127.0.0.1:8000/docs
```

Show the endpoints for learner plan, assessment, final exam submission, and manager insights.

## 6. Engineering Highlights

- 10 specialized agents
- 18 Microsoft certification tracks
- Synthetic Foundry/Fabric/Work IQ layers
- Largest Remainder study allocation
- Concurrent curation, planning, and quiz generation
- Guardrail validation at agent boundaries
- Fast mock mode with no credentials
- PDF exports
- Badge persistence
- FastAPI and Docker deployment path

## 7. Production Story

For production, the FastAPI backend can be deployed as an Azure container endpoint or Foundry Hosted Agent, then connected to Copilot Studio through OpenAPI custom actions.
