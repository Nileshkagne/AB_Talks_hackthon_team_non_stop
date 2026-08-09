# 🎬 AI Technical Evaluation Agent — Video Presentation & System Architecture Guide

> **Purpose**: A comprehensive, step-by-step video script, technical explainer, and architectural breakdown to present and demonstrate the **AI Technical Evaluation Agent** for hackathon demos, videos, and technical presentations.

---

## 📌 1. Video Overview & Elevator Pitch

### 🎙️ Suggested Opening Script (0:00 - 0:45)
> *"Hello everyone! Welcome to our demonstration of the **AI Technical Evaluation Agent** — an adaptive, persona-driven AI interviewer built for evaluating candidate progress across an intensive 31-day AI engineering curriculum.*
>
> *Our core philosophy is simple: **'Same interviewer, different interview.'** Traditional technical screeners ask static, rigid question sets. Our agent dynamically tailors every single interview to the specific candidate — calculating personalized starting difficulties, prioritizing their historical weak topics, conducting intelligent follow-ups based on their actual answers, and providing actionable multi-dimensional feedback."*

---

## 🏗️ 2. High-Level System Architecture

```
  ┌────────────────────────────────────────────────────────────────────────┐
  │                           REACT + VITE SPA                             │
  │  (Dark/Light Themes, Candidate Selector, Real-Time Chat canvas, PDF)   │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │  POST /api/interview (JSON)
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                         FASTAPI BACKEND SERVER                         │
  │  - CORS Protection (Vercel & Local Regex)                              │
  │  - Session Orchestration & Input Validation (Max 4000 chars)           │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                      LANGGRAPH STATE MACHINE                           │
  │  ┌──────────────┐   ┌───────────────────┐   ┌───────────────────────┐  │
  │  │ select_topic │──>│ generate_question │──>│    evaluate_answer    │  │
  │  └──────────────┘   └───────────────────┘   └───────────────────────┘  │
  │         ▲                                               │              │
  │         └──────────────── update_state <────────────────┘              │
  │                                 │                                      │
  │                                 ▼ (If Done: 8-12 turns & 4 days)       │
  │                         generate_feedback                              │
  └─────────────────┬──────────────────────────────────┬───────────────────┘
                    │                                  │
                    ▼                                  ▼
 ┌──────────────────────────────────────┐  ┌───────────────────────────────┐
 │          GEMINI LLM CLIENT           │  │      SUPABASE POSTGRESQL      │
 │ Automatic Model Fallback Chain:      │  │ Persistent Session Storage:   │
 │ 2.5-flash -> 2.0-flash -> 1.5-flash │  │ - interview_sessions          │
 └──────────────────────────────────────┘  │ - interview_messages          │
                                           │ - answer_evaluations          │
                                           │ - interview_feedback          │
                                           └───────────────────────────────┘
```

---

## 🧠 3. How the System Works (Core Engineering Deep Dive)

### 3.1 Candidate Personalization & Adaptive Difficulty
* **Initial Profile Derivation**:
  When an interview begins, the backend inspects the candidate's historical record from `candidates.json`:
  $$\text{Initial Difficulty} = \text{Clamp}_{1.0}^{10.0}\left( 3.0 + 0.4 \times \text{years\_exp} + 1.5 \times \frac{\text{first\_try\_passes}}{\text{missions\_done}} + \Delta_{\text{role}} \right)$$
  * *Example*: A senior candidate (9 yrs exp) starts at **Intermediate/Advanced (7.0)** difficulty, while a junior candidate starts at **Foundation (4.0)**.
* **Topic Routing Engine**:
  The system computes candidate weakness scores for each curriculum day:
  $$\text{Topic Score} = 0.5 \times (10 - \text{performance\_score}) + 0.3 \times \text{role\_weight} + 0.2 \times \text{uncovered\_bonus}$$
  It prioritizes topics where the candidate previously struggled or skipped missions, ensuring targeted assessment while guaranteeing coverage of at least 4 distinct curriculum days.

---

### 3.2 The Turn-by-Turn LangGraph Workflow

Every HTTP request to `POST /api/interview` executes a stateless, re-hydrated LangGraph state machine:

1. **State Rehydration**: The backend loads session history from Supabase.
2. **`select_topic` Node**: Determines whether to continue the current topic with a follow-up (max 2 follow-ups) or switch to the next best topic.
3. **`generate_question` Node**: 
   - Invokes Google Gemini with an **Interviewer System Prompt**.
   - If `follow_up_count > 0`, the prompt strictly enforces that the follow-up question **must cite specific technical claims or gaps** from the candidate's last answer.
   - Includes **Intro Mode** on Turn 1 to deliver a warm, personalized greeting.
4. **Candidate Answer Submission**: The candidate types their response in the React UI.
5. **`evaluate_answer` Node**:
   - Evaluates the answer against the specific day's learning objectives using a 5-metric rubric:
     $$\text{Overall Score} = 0.35(\text{Correctness}) + 0.25(\text{Depth}) + 0.20(\text{Reasoning}) + 0.10(\text{Practicality}) + 0.10(\text{Communication})$$
   - Extracts specific `missing_concepts` and generates a 1-2 sentence evaluation summary.
6. **`update_state` Node**:
   - Dynamically nudges difficulty up (+0.5) if score $\ge 7.5$, or down (-0.5) if score $< 5.5$.
7. **Decision Router (`decide_next_action`)**:
   - Evaluates python-enforced termination guardrails:
     - Total questions $\ge 8$ and $\le 12$.
     - Distinct curriculum days covered $\ge 4$.
     - If conditions are met, routes to `generate_feedback`. Otherwise, loops back to `select_topic`.
8. **`generate_feedback` Node**:
   - Synthesizes an executive performance report: Overall Percentage (0-100%), per-category breakdown, grounded strengths & gaps citing specific candidate quotes, actionable next steps, written fluency score, and a warm closing remark.

---

### 3.3 Production Resilience & Security Guardrails

* **Prompt Injection Defenses**: Candidate input is treated strictly as untrusted data inside double quotes; system prompts explicitly instruct LLMs to ignore candidate instructions attempting to alter scoring or reveal prompts.
* **Gemini Multi-Model Fallback Chain**: If a Gemini model hits a 429 rate limit or quota error, the custom LLM client seamlessly falls back: `gemini-2.5-flash` $\rightarrow$ `gemini-2.0-flash` $\rightarrow$ `gemini-1.5-flash`.
* **Render Free-Tier Cold-Start Tolerance**: The frontend API client uses non-blocking fetch calls and displays an active "Initiating Session..." state during Render's 30-50 second container spin-up.
* **SPA Routing & CORS**: `vercel.json` rewrite rules eliminate 404s on hard refresh, while `main.py` CORS middleware dynamically matches live `.vercel.app` production domains.

---

## 🎬 4. Step-by-Step Video Demonstration Script

Follow this exact walkthrough during your screen recording:

| Time | Screen | Action / What to Click | What to Say (Script) |
| --- | --- | --- | --- |
| **0:00 - 0:30** | **Home Page** | Show landing page, toggle Dark/Light theme button in header. | *"Here is the landing page of our application. Notice the application-wide Dark and Light theme toggle adhering to WCAG AA contrast standards. Candidates can select their profile from the cohort list."* |
| **0:30 - 1:00** | **Candidate Select** | Select **Sarah Johnson** (Senior Data Engineer, 9 yrs exp) then click **Start Technical Interview**. | *"We'll select Sarah Johnson, a Senior Data Engineer. The system analyzes her profile and cohort history to initialize a customized evaluation session with a higher starting difficulty."* |
| **1:00 - 2:00** | **Live Interview** | Show the warm personalized intro greeting. Type a technical answer about RAG pipelines / embeddings. | *"Notice the warm interviewer greeting acknowledging Sarah by name and role. As Sarah answers, the agent evaluates her response against curriculum objectives in real-time, tracking covered concepts and adjusting question difficulty dynamically."* |
| **2:00 - 2:30** | **Follow-up Question** | Show the AI interviewer asking a follow-up question referencing specific terms from the candidate's previous response. | *"Notice how the interviewer doesn't just ask random questions — it picks up on Sarah's specific mention of vector search and asks a targeted follow-up on HNSW index trade-offs."* |
| **2:30 - 3:15** | **Completion & Results** | Complete the final question. Show the **Completion Modal** then transition to **Results Page**. | *"Upon completing the required curriculum days and question count, the session finishes cleanly with a personalized closing remark. The candidate is presented with their final assessment dashboard."* |
| **3:15 - 4:00** | **Feedback & PDF Export** | Show overall percentage ring, category bars, grounded strengths/gaps, fluency score, and click **Download Official Assessment Report (PDF)**. | *"The results page features a multi-dimensional performance breakdown, writing fluency analysis, grounded strengths citing actual candidate quotes, and actionable next steps. Candidates can export an official, multi-page vector PDF report."* |

---

## 🚀 5. Quick Links & Live URLs for Presentation

- 🌐 **Live Website (Vercel)**: [https://ab-talks-hackthon-team-non-stop.vercel.app](https://ab-talks-hackthon-team-non-stop.vercel.app)
- ⚙️ **Live API Backend (Render)**: [https://ab-talks-hackthon-team-non-stop.onrender.com](https://ab-talks-hackthon-team-non-stop.onrender.com)
- 🩺 **Health Check**: [https://ab-talks-hackthon-team-non-stop.onrender.com/health](https://ab-talks-hackthon-team-non-stop.onrender.com/health)
- 💻 **GitHub Repository**: [https://github.com/Nileshkagne/AB_Talks_hackthon_team_non_stop](https://github.com/Nileshkagne/AB_Talks_hackthon_team_non_stop)
