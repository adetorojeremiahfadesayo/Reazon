# 🤖 Microsoft Copilot Studio Integration: Production Architecture

This guide describes how to deploy and integrate the **CertPrep-Ex 10-Agent System** as a native Microsoft 365 Copilot Extension using **Microsoft Copilot Studio**.

---

## 🏛️ Integration Architecture

Instead of serving the UI from Streamlit, the production-grade deployment exposes our Python orchestration engine via a REST API and registers it as a conversational extension inside Microsoft Teams and Microsoft 365 Copilot.

```
┌────────────────────────────────────────────────────────┐
│             Microsoft Teams / M365 Copilot             │
│    (Learner chats, answers quizzes, receives alerts)   │
└───────────────────────────▲────────────────────────────┘
                            │ Conversational Channel
┌───────────────────────────▼────────────────────────────┐
│               Microsoft Copilot Studio                 │
│  (Custom Action, Generative Topics, & Orchestration)   │
└───────────────────────────▲────────────────────────────┘
                            │ REST API + JSON Actions
┌───────────────────────────▼────────────────────────────┐
│            Azure AI Foundry Agent Service              │
│    (Exposes our 10-agent orchestration container)      │
└───────────────────────────▲────────────────────────────┘
                            │ Reads contextual signals
┌───────────────────────────┴────────────────────────────┐
│             Microsoft IQ Grounding Layers              │
│   • Foundry IQ (Search indices & Curated Guides)       │
│   • Fabric IQ (SQL Ontology & Pass thresholds)         │
│   • Work IQ (M365 Graph calendar & focus hours)        │
└────────────────────────────────────────────────────────┘
```

---

## 🛠️ Step-by-Step Integration Guide

### Step 1: Containerize and Host the Agent Backend
We package our `src/` orchestrator as a lightweight FastAPI service, wrap it in a Docker container, and deploy it to **Azure AI Foundry Hosted Agents**:
- **Endpoint 1:** `POST /api/learner/profile` - Triggers input audit and returns `LearnerProfile`.
- **Endpoint 2:** `POST /api/learner/plan` - Runs scheduling largest-remainder algorithm, returning a weekly Gantt-aligned study plan.
- **Endpoint 3:** `POST /api/learner/assessment` - Generates a 5-question quiz with grounding citations.
- **Endpoint 4:** `POST /api/manager/insights` - Runs manager diagnostics, mapping risks and buddy pairs.

---

### Step 2: Configure Custom Connectors in Copilot Studio
1. Open the [Microsoft Copilot Studio Portal](https://copilotstudio.microsoft.com/).
2. Select **Actions** -> **Add an Action** -> **Custom Connector**.
3. Import the OpenAPI definition (Swagger JSON) of our hosted FastAPI service.
4. Set up authentication using **Azure Active Directory (OAuth 2.0 / Entra ID)** so that the user's M365 identity (Work IQ Context) is securely forwarded to the agent backend.

---

### Step 3: Define Conversational Topics and Prompts
Create a conversational trigger topic in Copilot Studio (e.g., "Prepare for Azure Exam"):
1. **User Utterance:** "Help me prepare for my AZ-204 exam."
2. **Copilot Action:** Calls `LearnerProfilerAgent` connector, passing the user's details and active Entra ID.
3. **Condition Check:** If profile is returned, call `StudyPlanAgent` to generate the schedule.
4. **Output Rendering:** Render the schedule as an **Adaptive Card** inside the chat window.

---

## 🎨 Interactive Adaptive Card Payload Example
When the `StudyPlanAgent` returns the study schedule, Copilot Studio displays it as a native visual widget (no Streamlit required):

```json
{
  "type": "AdaptiveCard",
  "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
  "version": "1.3",
  "body": [
    {
      "type": "TextBlock",
      "text": "📅 Your Personalized Study Schedule",
      "weight": "Bolder",
      "size": "Medium",
      "color": "Accent"
    },
    {
      "type": "FactSet",
      "facts": [
        {
          "title": "Certification:",
          "value": "AZ-204: Azure Developer"
        },
        {
          "title": "Total Study Time:",
          "value": "20 Hours"
        },
        {
          "title": "Workload Status:",
          "value": "⚠️ Week 2 Adjusted for Meeting Overload (Work IQ)"
        }
      ]
    },
    {
      "type": "TextBlock",
      "text": "Week-by-Week Focus Modules:",
      "weight": "Bolder",
      "spacing": "Medium"
    },
    {
      "type": "Container",
      "items": [
        {
          "type": "TextBlock",
          "text": "• Week 1: Develop Azure compute solutions (8h)",
          "wrap": true
        },
        {
          "type": "TextBlock",
          "text": "• Week 2: Develop for Azure storage (3h) *[ADJUSTED]*",
          "wrap": true,
          "color": "Warning"
        }
      ]
    }
  ],
  "actions": [
    {
      "type": "Action.Submit",
      "title": "Take Mock Assessment",
      "data": {
        "action": "start_quiz",
        "cert": "AZ-204"
      }
    }
  ]
}
```

---

## 🔒 Security, Compliance, & PII Management
By deploying via Copilot Studio, we inherit Microsoft's tenant isolation security out-of-the-box:
1. **No Data Leakage:** All customer data and transcripts remain inside the corporate tenant boundaries.
2. **Access Control:** Only managers can query endpoints mapped to the `ManagerInsightsAgent`, enforced by Entra ID group checks.
3. **Data Residency:** All data grounding search files processed by Foundry IQ remain hosted within the Azure region chosen.
