# AI Interview Agent — Implementation Plan
### ABTalks Vibe Coding Hackathon — "The Interview Agent: Build the interviewer, not the interview"

---

## 1. Executive Summary

We are building an **Adaptive AI Technical Interviewer**: a backend agent that conducts a multi-turn, personalized technical interview based on a candidate's progress through a 31-day AI engineering cohort, and a thin React frontend to run it.

Core product truth: **same interviewer, different interview.** Two candidates with different `candidates.json` profiles must walk different question paths through the same 31-day `curriculum.json`, because the agent scores topics, adapts difficulty, and generates follow-ups based on each answer.

Hard constraints from the technical spec (authoritative — see §38 source of truth):
- Single endpoint: `POST /api/interview`, no auth, state keyed by `sessionId`.
- ≥8 questions, covering ≥4 distinct curriculum days.
- Genuine follow-ups derived from the candidate's actual answers.
- Final response: `{ reply, done: true, feedback: { summary, strengths[], gaps[], next[] } }`.

Locked stack: **React + Vite + Tailwind** → **FastAPI + Pydantic + LangGraph** → **Gemini** for language generation, **Supabase Postgres** for persistent state, `curriculum.json` / `candidates.json` as static data. Deterministic Python logic — not the LLM — enforces the 8-question/4-day/12-max rules.

This document is the plan only. No application code is generated here.

---

## 2. Final Architecture

```
                          USER
                            │
                            ▼
                  React + Vite + Tailwind  (Netlify)
                            │  HTTPS, VITE_API_URL
                            ▼
                     FastAPI  (backend host)
                     POST /api/interview
                            │
                            ▼
                        LangGraph
              interview state machine (per-request run)
          ┌─────────────┬─────────────┬──────────────┐
          ▼              ▼             ▼              ▼
   candidate_service curriculum_   interview_    evaluation_
   (candidates.json)  service       service       service
                    (curriculum.json)  │              │
                                       ▼              ▼
                              Supabase PostgreSQL   Gemini API
                              (sessions, messages,  (question gen,
                               evaluations,          answer eval,
                               feedback)             feedback gen)
```

Key architectural decision: because the HTTP contract is **stateless, one-request-per-turn**, LangGraph is **not** used as a long-running persisted checkpoint process. It is instead **re-invoked per request**: on every call we rehydrate an `InterviewState` object from Supabase rows, run the graph one step (or one "superstep" of nodes) to produce the next reply, then persist the resulting state back to Supabase before returning. This keeps the backend compatible with serverless/stateless hosting and avoids relying on in-memory LangGraph checkpointers, which would not survive a cold start or a second replica.

---

## 3. Technology Decisions and Justification

| Layer | Choice | Why |
|---|---|---|
| Frontend | React + Vite + Tailwind | Fast to scaffold for a hackathon, matches locked stack, no SSR complexity needed for 3 screens. |
| Backend | FastAPI + Pydantic | Async, typed request/response validation matching the exact API contract, easy CORS setup, works on serverless-friendly hosts (e.g. Render/Railway/Fly). |
| Orchestration | LangGraph | Gives an explicit, inspectable node graph for the interview flow (generate → evaluate → decide → generate), which is easy to explain to judges and to extend with follow-up branches. |
| LLM | Gemini API | Locked choice; used only for language generation (questions, evaluation rationale, feedback prose), never for enforcing hard limits. |
| Database | Supabase PostgreSQL | Real persistent store required because SQLite is explicitly disallowed in production and the backend must be stateless between requests; Supabase gives managed Postgres with minimal setup. |
| Static data | `curriculum.json`, `candidates.json` | Supplied by the hackathon; no reason to move them into the DB — they're read-only reference data, loaded once per process and cached in memory. |
| Testing | Pytest | Standard, fast, integrates with FastAPI's TestClient. |
| Frontend hosting | Netlify | Locked choice; trivial static hosting + build pipeline for Vite. |
| Backend hosting | Any FastAPI-compatible cloud host (Render / Railway / Fly.io — confirm current free-tier availability at implementation time) | Needs to run a long-lived Python process (not a pure static host); must support env vars and outbound HTTPS to Gemini + Supabase. |

Explicitly **not** used and why: SQLite in prod (no durability across instances/redeploys), Redis (no caching need at this scale), ChromaDB/RAG (no retrieval requirement — curriculum is small enough for direct lookup), MCP (no external tool-use requirement in the interview loop itself), CrewAI/LangSmith (LangGraph alone is sufficient; extra frameworks add risk without product value), Kubernetes (single small service, not needed), auth/user accounts/voice/mobile (out of scope per spec).

---

## 4. Database Schema (Supabase PostgreSQL)

```sql
-- 1. One row per interview session
create table interview_sessions (
  session_id           text primary key,
  candidate_id         text not null,
  status                text not null default 'active',   -- active | completed | abandoned
  question_count        int  not null default 0,
  follow_up_count        int  not null default 0,           -- follow-ups on the CURRENT topic
  current_day           int,
  current_topic          text,
  difficulty             text not null default 'intermediate', -- foundation|intermediate|advanced|expert
  covered_days           int[] not null default '{}',
  strengths              text[] not null default '{}',
  weaknesses              text[] not null default '{}',
  created_at             timestamptz not null default now(),
  updated_at             timestamptz not null default now()
);

-- 2. Full transcript, one row per turn
create table interview_messages (
  id               bigserial primary key,
  session_id        text not null references interview_sessions(session_id) on delete cascade,
  role             text not null,          -- interviewer | candidate
  content          text not null,
  question_number  int,
  curriculum_day   int,
  topic            text,
  question_type    text,                    -- conceptual|why|comparison|debugging|architecture|trade_off|scenario|production
  created_at       timestamptz not null default now()
);

-- 3. One row per candidate answer evaluation
create table answer_evaluations (
  id                   bigserial primary key,
  session_id            text not null references interview_sessions(session_id) on delete cascade,
  question_number       int not null,
  question              text not null,
  answer                text not null,
  curriculum_day        int,
  topic                 text,
  correctness           numeric,
  technical_depth       numeric,
  reasoning             numeric,
  practicality          numeric,
  communication         numeric,
  overall_score         numeric,
  confidence            numeric,
  missing_concepts      text[] default '{}',
  follow_up_needed      boolean default false,
  evaluation_summary    text,
  created_at            timestamptz not null default now()
);

-- 4. One row per completed interview
create table interview_feedback (
  session_id       text primary key references interview_sessions(session_id) on delete cascade,
  summary          text not null,
  strengths        text[] not null default '{}',
  gaps             text[] not null default '{}',
  next_steps        text[] not null default '{}',
  overall_score     numeric,
  created_at        timestamptz not null default now()
);

create index idx_messages_session on interview_messages(session_id);
create index idx_evaluations_session on answer_evaluations(session_id);
create index idx_sessions_status on interview_sessions(status);
```

`interview_sessions` is the "state snapshot" the graph rehydrates from on every request; `interview_messages` and `answer_evaluations` are the append-only history the LLM prompts are built from.

---

## 5. API Contract (must match technical-spec.md exactly)

```
POST /api/interview
Content-Type: application/json
No auth.
```

**Turn 1 — start**
```json
// Request
{ "sessionId": "abc-123", "candidate": { ...candidate.json object... } }

// Response
{ "reply": "Welcome. Let's begin your interview. ...<first question>", "done": false }
```

**Turn 2..N — conversation**
```json
// Request
{ "sessionId": "abc-123", "message": "candidate's answer text" }

// Response
{ "reply": "<next question or follow-up>", "done": false }
```

**Final turn — completion**
```json
{
  "reply": "Interview completed.",
  "done": true,
  "feedback": {
    "summary": "string",
    "strengths": ["string", "..."],
    "gaps": ["string", "..."],
    "next": ["string", "..."]
  }
}
```

Backend request routing rule: if the body contains `candidate` → treat as session start (create row if `sessionId` not already `active`; if it already exists, return the existing state's last reply idempotently rather than erroring). If the body contains `message` and no `candidate` → treat as a conversation turn; if `sessionId` is unknown, return HTTP 404 with a clear error body (see §12 error handling) rather than silently creating a new session.

---

## 6. LangGraph State Design

```python
class InterviewState(TypedDict):
    session_id: str
    candidate: dict            # raw candidate.json profile
    profile: dict               # derived InterviewProfile (see §11)
    question_count: int
    follow_up_count: int
    covered_days: list[int]
    current_day: int | None
    current_topic: str | None
    difficulty: str              # foundation|intermediate|advanced|expert
    last_question: str | None
    last_question_type: str | None
    last_answer: str | None
    last_evaluation: dict | None
    strengths: list[str]
    weaknesses: list[str]
    done: bool
    reply: str | None
    feedback: dict | None
```

This state is (a) reconstructed from `interview_sessions` + the tail of `interview_messages`/`answer_evaluations` at the start of every request, (b) mutated by graph nodes in memory during that single request, and (c) written back to Postgres before the HTTP response is returned. LangGraph itself does not need a persisted checkpointer for this project — Postgres *is* the checkpoint.

---

## 7. LangGraph Node-by-Node Workflow

**Start-of-interview run** (`candidate` present):
```
START → load_or_create_session → build_profile → select_topic
      → generate_question → persist_state → END (return reply)
```

**Conversation-turn run** (`message` present):
```
START → load_session → save_candidate_answer → evaluate_answer
      → update_state (scores, covered_days, strengths/weaknesses)
      → decide_next_action ──┬─ follow_up ────────┐
                              ├─ new_topic ─────────┤→ generate_question → persist_state → END
                              └─ finish ──→ generate_feedback → persist_feedback → END
```

Node responsibilities:
- `load_or_create_session` / `load_session`: read from `interview_sessions`; 404 if turn-2+ session is missing.
- `build_profile`: deterministic transform of `candidate.json` → `InterviewProfile` (§11).
- `select_topic`: deterministic scoring over curriculum days (§12) → sets `current_day`/`current_topic`/initial `difficulty`.
- `generate_question`: single Gemini call, structured-output prompt (`prompts/interviewer.md`), given profile + current topic + difficulty + recent Q/A history (to avoid repeats) + question type target.
- `save_candidate_answer`: insert into `interview_messages` (role=candidate).
- `evaluate_answer`: single Gemini call, structured-output prompt (`prompts/evaluator.md`) → the evaluation JSON (§14); insert into `answer_evaluations`.
- `update_state`: pure Python — updates `question_count`, `covered_days`, `difficulty` (per §15), `strengths`/`weaknesses`.
- `decide_next_action`: pure Python deterministic gate (§16) — this is the node that enforces 8/4/12.
- `generate_feedback`: single Gemini call, structured-output prompt (`prompts/feedback.md`), given the full transcript + evaluations.
- `persist_state` / `persist_feedback`: write `interview_sessions` row (+ `interview_feedback` row on completion).

Exactly one Gemini call happens per HTTP request (two on the very last turn: evaluate the final answer, then generate feedback) — this keeps latency and cost predictable.

---

## 8. Candidate Personalization Algorithm

Deterministic transform, no LLM involved:

```python
def build_profile(candidate: dict, curriculum: dict) -> dict:
    strength_topics, weak_topics, skipped_topics = [], [], []
    for mission in candidate["missions"]:
        day = mission["day"]
        topic = curriculum_topic_for_day(day, curriculum)
        if mission["status"] == "passed" and mission.get("firstTry", False):
            strength_topics.append(topic)
        elif mission["status"] == "failed":
            weak_topics.append(topic)
        elif mission["status"] == "skipped":
            skipped_topics.append(topic)

    signals = candidate["learningSignals"]
    completion_rate = signals["missionsCompleted"] / candidate["totalMissions"]
    first_try_rate  = signals["missionsFirstTry"] / max(signals["missionsCompleted"], 1)
    consistency     = signals["commitDays"] / candidate["cohortDays"]

    confidence_score = 0.4*completion_rate + 0.4*first_try_rate + 0.2*consistency

    if confidence_score >= 0.8:  difficulty = "advanced"
    elif confidence_score >= 0.5: difficulty = "intermediate"
    else:                          difficulty = "foundation"

    # experience nudges difficulty by at most one level
    if candidate["yearsExperience"] >= 5 and difficulty != "advanced":
        difficulty = bump_up(difficulty)
    if candidate["yearsExperience"] <= 1 and difficulty != "foundation":
        difficulty = bump_down(difficulty)

    return {
        "candidate_id": candidate["id"],
        "role": candidate["role"],
        "experience": candidate["yearsExperience"],
        "strength_topics": dedupe(strength_topics),
        "weak_topics": dedupe(weak_topics),
        "skipped_topics": dedupe(skipped_topics),
        "confidence_level": confidence_score,
        "difficulty": difficulty,
    }
```

This runs once, at session start, and is stored implicitly via `interview_sessions.difficulty`/`covered_days` plus recomputed on demand from `candidate.json` (cheap — no need to persist the full profile object).

---

## 9. Topic Selection Algorithm

Run at `select_topic` and at every `new_topic` branch of `decide_next_action`. All curriculum days are scored; the highest-scoring **uncovered** day is chosen (ties broken by lowest day number for determinism).

```python
def score_day(day: dict, profile: dict, covered_days: set[int]) -> float:
    role_relevance      = ROLE_TOPIC_WEIGHTS.get(profile["role"], {}).get(day["module"], 0.5)  # 0..1
    weakness             = 1.0 if day["topic"] in profile["weak_topics"] else (
                            0.6 if day["topic"] in profile["skipped_topics"] else 0.2)
    curriculum_importance = day.get("importance", 0.5)          # authored weight per day, from curriculum.json or a lookup table
    coverage_need         = 1.0 if len(covered_days) < 4 else 0.4  # push hard for day-diversity early
    difficulty_fit         = 1.0 - abs(DIFFICULTY_RANK[profile["difficulty"]] - DIFFICULTY_RANK[day.get("level", "intermediate")]) / 3
    already_covered_penalty = 1.0 if day["day"] in covered_days else 0.0

    return (0.25*role_relevance + 0.30*weakness + 0.20*curriculum_importance
            + 0.15*coverage_need + 0.10*difficulty_fit) - already_covered_penalty
```

`ROLE_TOPIC_WEIGHTS` is a small static lookup (e.g. "AI Engineer" weights RAG/agents/MCP modules higher; "IT Support Specialist" weights deployment/tooling/security higher) — explainable in a table in `README.md`, not hidden in a prompt. Weak/failed topics are intentionally weighted highest (0.30) so struggling candidates get probed on their actual gaps, which is the product's core differentiator.

---

## 10. Question Generation Strategy

- One Gemini call per question, prompt = `prompts/interviewer.md` + structured context block: candidate role/experience, current day's title/objectives/tools, target difficulty, target question type, and the last 2–3 Q/A pairs (to avoid repetition and keep continuity).
- Question type is chosen deterministically before the call, cycling/weighted across the 8 types in §18 of the source brief (conceptual, why/how, comparison, debugging, architecture, trade-off, scenario, production), biased toward "conceptual/why" early in a topic and "architecture/production" only at `advanced`/`expert` difficulty.
- Output is constrained via Pydantic (`response_mime_type: application/json` + schema) to `{ "question": str, "type": str }` — no free-form chain-of-thought is requested or stored.
- The prompt explicitly instructs Gemini not to repeat prior questions and not to reveal scoring/evaluation to the candidate.

## 11. Answer Evaluation Strategy

- One Gemini call, prompt = `prompts/evaluator.md`, structured output matching the `answer_evaluations` schema (§4): `correctness, technical_depth, reasoning, practicality, communication` (0–10 each), `overall_score` (weighted mean), `confidence` (0–1), `missing_concepts[]`, `follow_up_needed` (bool), `evaluation_summary` (1–2 sentences, candidate-safe language, never shown verbatim to the user).
- Evaluation is graded **against the specific curriculum day's stated objectives/tools**, not generic knowledge — this is what makes follow-ups feel targeted rather than generic.

## 12. Adaptive Follow-up Logic

`decide_next_action` (pure Python, reads `last_evaluation` + counters):

```python
def decide_next_action(state):
    if state.question_count >= MAX_QUESTIONS:                       # 12
        return "finish"
    if state.question_count >= MIN_QUESTIONS and len(state.covered_days) >= MIN_DAYS:  # 8 and 4
        return "finish"
    if state.question_count >= MIN_QUESTIONS and len(state.covered_days) < MIN_DAYS:
        return "new_topic"                                           # force day diversity
    if (state.last_evaluation["follow_up_needed"]
            and state.follow_up_count < MAX_FOLLOWUPS_PER_TOPIC):    # 2
        return "follow_up"
    return "new_topic"
```

Follow-up question generation reuses `generate_question` but with an added prompt instruction to specifically address `last_evaluation.missing_concepts`, e.g. "the candidate mentioned raising top-k but did not mention reranking or similarity thresholds — ask a targeted follow-up on that gap" (concepts passed as structured data, not as a rendered sentence the model just repeats).

## 13. Difficulty Progression

Applied in `update_state` after each evaluation:

```python
if evaluation.overall_score >= 8.5:   difficulty = bump_up(difficulty)     # cap at "expert"
elif evaluation.overall_score < 6.0:  difficulty = bump_down(difficulty)   # floor at "foundation"
# 6.0–8.5 → unchanged
```

Difficulty also seeds the *initial* value from the candidate profile (§11 experience/confidence), so two candidates starting on the same day can still get differently-pitched first questions.

---

## 14. Interview Completion Logic

Enforced entirely in `decide_next_action` (§16 above), constants:

```python
MIN_QUESTIONS = 8
MAX_QUESTIONS = 12
MIN_CURRICULUM_DAYS = 4
MAX_FOLLOWUPS_PER_TOPIC = 2
```

This guarantees the two hard hackathon requirements even if Gemini's own judgment would end the interview earlier or later — the LLM proposes questions/evaluations, Python enforces the contract.

## 15. Final Feedback Generation

At `finish`, one Gemini call with the *entire* transcript + evaluations + profile, prompt = `prompts/feedback.md`, structured output exactly matching:

```json
{ "summary": str, "strengths": [str, ...], "gaps": [str, ...], "next": [str, ...] }
```

Persisted to `interview_feedback`, then mapped 1:1 into the final HTTP response (`next_steps` column → `next` field, everything else matches the API contract directly).

---

## 16. Backend Architecture

```
backend/app/
  main.py                  # FastAPI app, CORS, router mount
  api/interview.py         # POST /api/interview handler — thin, delegates to interview_service
  agent/
    graph.py                # LangGraph graph definition, wires nodes below
    state.py                # InterviewState TypedDict
    nodes.py                 # all node functions (§7)
    router.py                 # decide_next_action + topic scoring (§9, §14)
  services/
    candidate_service.py      # load/lookup candidates.json, in-memory cache
    curriculum_service.py      # load/lookup curriculum.json, in-memory cache
    interview_service.py        # orchestrates: rehydrate state → run graph → persist → build HTTP response
    evaluation_service.py        # Gemini call wrappers for evaluate/feedback (thin, testable)
  llm/gemini.py                  # Gemini client wrapper, structured-output helper, retry/timeout
  database/
    connection.py                 # Supabase/Postgres client init (env-driven)
    repository.py                  # CRUD for the 4 tables (§4)
  schemas/
    interview.py                    # Pydantic request/response models matching §5 exactly
    feedback.py                      # Pydantic feedback model
```

`api/interview.py` stays deliberately thin (parse request → call `interview_service.handle_turn(...)` → return response) so the contract layer can't drift from the technical spec even as agent logic evolves.

## 17. Frontend Architecture

Three screens only (per §24 of the brief), talking to the backend through `services/api.js` (single `postInterviewTurn(sessionId, payload)` function reading `VITE_API_URL`):

- `pages/Home.jsx` — pick/enter candidate, show role/experience, "Start Interview" → generates `sessionId` (uuid v4) client-side, calls start turn.
- `pages/Interview.jsx` — shows `QuestionCard`, `AnswerInput`, `ProgressBar` (question_count is inferred from local turn count, not exposed by backend beyond `done`), submits `message`, loops until `done: true`.
- `pages/Results.jsx` — renders `FeedbackCard` from the final `feedback` object.

No internal scores, difficulty, or evaluation data are ever rendered to the user — only `reply` text and, at the end, the feedback block.

---

## 18. Environment Variables

**Backend** (`.env`, never committed — `.env.example` committed instead):
```env
GEMINI_API_KEY=
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
ALLOWED_ORIGINS=https://<netlify-app>.netlify.app,http://localhost:5173
```

**Frontend** (`.env`, Vite-prefixed so it's safe to expose — it's just a URL):
```env
VITE_API_URL=https://<backend-host>/api
```

No secret ever reaches the frontend bundle; `SUPABASE_SERVICE_ROLE_KEY` and `GEMINI_API_KEY` live only in backend process env.

---

## 19. Project Folder Structure

```
ai-interview-agent/
├── frontend/
│   ├── src/
│   │   ├── components/ (InterviewHeader, QuestionCard, AnswerInput, ProgressBar, FeedbackCard)
│   │   ├── pages/ (Home, Interview, Results)
│   │   ├── services/api.js
│   │   ├── App.jsx, main.jsx
│   ├── package.json, vite.config.js, .env.example
├── backend/
│   ├── app/ (main.py, api/, agent/, services/, database/, llm/, schemas/)
│   ├── data/ (curriculum.json, candidates.json)
│   └── requirements.txt
├── tests/ (test_api.py, test_interview.py, test_agent.py)
├── prompts/ (interviewer.md, evaluator.md, feedback.md)
├── PROMPTS.md
├── AI_USAGE_LOG.md
├── README.md
├── .env.example
└── .gitignore
```

---

## 20. Required API Keys / External Accounts

| Key / Account | Where used | How to obtain |
|---|---|---|
| `GEMINI_API_KEY` | Backend only — question generation, answer evaluation, feedback generation | Google AI Studio → create an API key for the Gemini API (free tier available; confirm current rate limits before the demo). |
| `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` | Backend only — Postgres access via Supabase client | Create a free Supabase project → Project Settings → API → copy Project URL and the `service_role` key (server-side only, never the `anon` key in the frontend). |
| Backend hosting account | Deploying FastAPI service | Whichever host is chosen (Render/Railway/Fly.io/etc.) — no API key needed at plan time, just an account + a deploy-time env var setup. |
| Netlify account | Frontend hosting | Free account, connect the GitHub repo, set `VITE_API_URL` as a Netlify environment variable. |
| GitHub account | Public repo, commit history, submission | Required by hackathon rules. |

No other third-party keys are needed — there is deliberately no vector DB, no auth provider, and no additional LLM provider in this design.

---

## 21. Error Handling

- Missing/invalid `sessionId` on a continuation turn → HTTP 404, `{"error": "session_not_found", "message": "..."}`.
- Malformed request body (fails Pydantic validation) → HTTP 422 (FastAPI default), no custom handling needed beyond clear field names in schemas.
- Gemini call fails/times out → retry once with backoff; on second failure, return a graceful in-domain fallback question (e.g. a pre-written fallback per difficulty level) rather than a raw 500, so a demo never visibly breaks; log the failure.
- Supabase write failure → return HTTP 500 with a generic message; never leak DB internals in the response body; log full detail server-side.
- Interview already `completed` and a new turn arrives → return the stored final `feedback` again (idempotent), don't error and don't restart.

## 22. Security Considerations

- No auth per spec, so treat every request as untrusted: validate `sessionId` format, cap message length, sanitize before interpolating into prompts (basic prompt-injection resistance — instruct the model explicitly to treat candidate input as data, not instructions).
- CORS locked to the known Netlify origin + localhost dev origin, not `*`.
- Service-role Supabase key and Gemini key only ever read from server-side env vars, never returned in any response, never logged in plaintext.
- Rate-limit-friendly: one Gemini call (two on the final turn) per HTTP request, no loops that could runaway-call the LLM.

---

## 23. Testing Strategy

**API tests** (`tests/test_api.py`): start turn returns `done:false` + non-empty `reply`; continuation turn with valid session succeeds; continuation with unknown session → 404; malformed body → 422; full simulated interview end-to-end reaches `done:true` with a well-formed `feedback` object.

**Interview rule tests** (`tests/test_interview.py`, using a mocked Gemini client returning fixed evaluation scores): interview never finishes before 8 questions; interview never finishes with fewer than 4 covered days even if scores are high early; interview is force-finished at 12 questions regardless of state; follow-up count never exceeds 2 per topic.

**Agent/unit tests** (`tests/test_agent.py`): `build_profile` produces expected `difficulty`/`weak_topics` for the CAND-003 (strong) and CAND-010 (weak) fixtures from `candidates.json`; `score_day` ranks a candidate's known weak day above an already-strong day; `decide_next_action` returns the correct branch for each of the 4 documented state combinations.

**Personalization test**: running the full simulated flow for CAND-003 and CAND-010 must produce different `current_topic`/`difficulty` sequences — this is the single most important test for the product story.

---

## 24. Deployment Architecture & Steps

1. **Supabase**: create project → run schema SQL (§4) → copy URL + service-role key.
2. **Backend**: push `backend/` to chosen host, set `GEMINI_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `ALLOWED_ORIGINS`; confirm `POST /api/interview` reachable over HTTPS; run one manual curl through a full interview.
3. **Frontend**: connect repo to Netlify, set `VITE_API_URL` to the deployed backend URL, deploy; verify CORS by running a full interview from the live site.
4. **Smoke test in production**: run both a strong-profile and weak-profile candidate through the live URL and confirm divergent question paths and valid final feedback JSON.

---

## 25. Git / Commit Strategy

Follow the ~22-commit incremental sequence from the brief (§30): scaffold → API contract → data loaders → DB schema → session service → LangGraph state → topic selection → question generation → evaluation → adaptive routing → completion rules → feedback → frontend wiring → error handling → tests → UI polish → backend deploy → frontend deploy → fixes → final e2e test. Each commit should be small enough to review individually — this directly protects against the "one huge final commit" disqualification signal.

## 26. PROMPTS.md / AI_USAGE_LOG.md Strategy

Update both files **the same day** as the corresponding commit, using the format from §31 of the brief (Task / Prompt / AI output / Changes made / Reason). Do this per phase, not retroactively at the end — a log written after the fact is exactly the "generic/unrelated" pattern the authenticity review flags.

---

## 27. Step-by-Step Implementation Order (Phases)

### Phase 0 — Repository & Environment
- **Goal**: working skeleton, no logic yet.
- **Files**: repo root, `.gitignore`, `.env.example`, `backend/requirements.txt`, `frontend/package.json`.
- **Dependencies**: fastapi, uvicorn, pydantic, langgraph, google-generativeai (or the current Gemini SDK), supabase-py, python-dotenv, pytest; frontend: react, vite, tailwindcss.
- **Tasks**: init git, create folder structure (§19), install deps, verify `uvicorn app.main:app` boots and `npm run dev` boots.
- **DoD**: empty FastAPI app returns 200 on `/health`; empty React app renders in browser.

### Phase 1 — Database
- **Goal**: Supabase schema live and reachable.
- **Files**: `backend/app/database/connection.py`, `repository.py`, SQL migration file.
- **Tasks**: create Supabase project, run schema (§4), write repository functions (`create_session`, `get_session`, `update_session`, `add_message`, `add_evaluation`, `save_feedback`).
- **DB changes**: all 4 tables + indexes created.
- **Testing**: repository functions covered by a small integration test against a test Supabase project (or local Postgres).
- **DoD**: can insert/read a session row from a script.

### Phase 2 — Static Data
- **Goal**: curriculum/candidate loaders with validation.
- **Files**: `services/candidate_service.py`, `services/curriculum_service.py`, `data/curriculum.json`, `data/candidates.json`.
- **Tasks**: load JSON once at startup into memory, expose `get_candidate(id)`, `get_curriculum_day(n)`, `all_days()`; validate against expected shape, fail fast on load if malformed.
- **DoD**: unit test loads both files and asserts 31 days / expected candidate count.

### Phase 3 — FastAPI Contract Layer
- **Goal**: `/api/interview` exists and matches the contract shape, backed by stub logic.
- **Files**: `main.py`, `api/interview.py`, `schemas/interview.py`.
- **Tasks**: Pydantic request/response models exactly matching §5; CORS middleware; a stub handler returning a hardcoded `{reply, done:false}` so the frontend can integrate early.
- **API changes**: `POST /api/interview` live.
- **Testing**: `test_api.py` — request/response shape tests pass against the stub.
- **DoD**: curl round-trip works end-to-end against the stub.

### Phase 4 — Interview State & LangGraph Skeleton
- **Goal**: real session lifecycle, no LLM yet (stubbed question text).
- **Files**: `agent/state.py`, `agent/graph.py`, `agent/nodes.py` (stub node bodies).
- **Tasks**: implement `InterviewState`, wire graph edges per §7, implement `load_or_create_session`/`load_session`/`persist_state` against Phase 1 repository.
- **DB changes**: sessions actually persist across two curl calls with the same `sessionId`.
- **DoD**: a 2-turn curl sequence shows `question_count` incrementing in the DB.

### Phase 5 — Interview Intelligence
- **Goal**: real personalization, topic selection, question generation, evaluation, follow-ups.
- **Files**: `agent/router.py`, `llm/gemini.py`, `services/evaluation_service.py`, `prompts/*.md`.
- **Tasks**: implement `build_profile` (§11), `score_day`/`select_topic` (§12), `generate_question`/`evaluate_answer` Gemini calls with structured output, `decide_next_action` (§16), difficulty progression (§13).
- **API changes**: none (still same contract), but replies are now real, adaptive text.
- **Testing**: `test_agent.py` unit tests (§23) with mocked Gemini responses.
- **DoD**: CAND-003 and CAND-010 fixtures produce visibly different topic/difficulty sequences.

### Phase 6 — Completion & Feedback
- **Goal**: interview reliably finishes and returns valid feedback.
- **Files**: `agent/nodes.py` (`generate_feedback`), `prompts/feedback.md`.
- **DB changes**: `interview_feedback` rows written.
- **Testing**: `test_interview.py` rule tests (§23).
- **DoD**: a full mocked run always ends with ≥8 questions, ≥4 days, valid `feedback` shape.

### Phase 7 — Frontend
- **Goal**: usable 3-screen UI wired to the real API.
- **Files**: all of `frontend/src/`.
- **Tasks**: Home → Interview → Results flow, loading/error states, uuid session generation.
- **DoD**: a person can complete a full interview through the browser against the local backend.

### Phase 8 — Testing Pass
- **Goal**: full suite green.
- **Tasks**: fill remaining gaps in §23's checklist, add any missing fixtures.
- **DoD**: `pytest` green in CI or locally with no skipped critical tests.

### Phase 9 — Deployment
- **Goal**: live public URLs.
- **Tasks**: per §24.
- **DoD**: production smoke test (§24 step 4) passes.

### Phase 10 — Hackathon Submission
- **Goal**: compliant submission package.
- **Tasks**: finalize `README.md` (architecture explanation + how to run), confirm `PROMPTS.md`/`AI_USAGE_LOG.md` are complete and match actual commits, verify repo visibility, verify live demo URL, run the submission checklist (§29) end-to-end.
- **DoD**: every item in §29 checked.

---

## 28. Testing Checklist

- [ ] Start turn returns valid `{reply, done:false}`
- [ ] Continuation turn with valid session works
- [ ] Continuation with unknown session → 404
- [ ] Malformed body → 422
- [ ] Full simulated interview reaches `done:true`
- [ ] ≥8 questions enforced
- [ ] ≥4 curriculum days enforced
- [ ] ≤12 questions enforced (hard stop)
- [ ] ≤2 follow-ups per topic enforced
- [ ] Difficulty increases on strong answers, decreases on weak ones
- [ ] Two different candidate fixtures produce different topic/difficulty paths
- [ ] Final `feedback` always has all 4 required fields, arrays are arrays
- [ ] Session state persists correctly across multiple requests
- [ ] Completed session doesn't accidentally restart

## 29. Deployment Checklist

- [ ] Supabase schema applied in production project
- [ ] Backend deployed with all 3 env vars set
- [ ] Backend `/api/interview` reachable over HTTPS
- [ ] CORS allows the deployed Netlify origin
- [ ] Frontend deployed with correct `VITE_API_URL`
- [ ] End-to-end interview run successfully on the live URLs
- [ ] No secrets present in frontend bundle or public repo

## 30. Hackathon Submission Checklist

- [ ] Public GitHub repository
- [ ] Commit history shows genuine incremental development (no single mega-commit)
- [ ] `README.md` explains architecture and how to run locally
- [ ] `PROMPTS.md` present and reflects actual prompts used
- [ ] `AI_USAGE_LOG.md` present and corresponds to implemented features
- [ ] Live demo URL functional
- [ ] Team registered per hackathon rules
- [ ] Submitted before deadline

## 31. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Gemini rate limits during live demo | Add retry/backoff + a static fallback question per difficulty so a hiccup never surfaces as a broken UI. |
| LLM occasionally returns malformed JSON | Enforce structured output schema at the API level; on parse failure, retry once, then fall back gracefully. |
| Session state desync (two requests race on the same `sessionId`) | Not expected under normal demo use (one browser tab); if needed, add a simple optimistic `updated_at` check on write. |
| Backend host cold starts add latency | Choose a host with fast cold starts, or add a lightweight warm-up ping before the demo. |
| Free-tier limits (Supabase/Gemini/hosting) reached mid-hackathon | Verify current limits at Phase 0 before committing to a host; keep interview length capped at 12 questions to bound cost per session. |
| Scope creep toward RAG/MCP/multi-agent frameworks | Explicitly excluded per §11 of the brief; revisit only if a judge requirement demands it. |

## 32. What Should NOT Be Implemented

Per the brief's explicit exclusions: SQLite in production, Redis, ChromaDB/RAG, MCP, CrewAI, LangSmith, Kubernetes, voice interfaces, authentication/user accounts, a mobile app, or a microservice split. All of these add implementation risk without being required by the actual problem statement or API contract.

## 33. Final End-to-End Request Lifecycle

```
Candidate opens Netlify app → clicks Start
  → frontend generates sessionId, POSTs {sessionId, candidate}
  → FastAPI → LangGraph: load_or_create_session → build_profile → select_topic
     → generate_question (Gemini) → persist_state
  → returns {reply: question, done:false}
Candidate answers → frontend POSTs {sessionId, message}
  → FastAPI → LangGraph: load_session → save_answer → evaluate_answer (Gemini)
     → update_state → decide_next_action
        → follow_up | new_topic → generate_question (Gemini) → persist_state → {reply, done:false}
        → finish → generate_feedback (Gemini) → persist_feedback → {reply:"Interview completed.", done:true, feedback}
Frontend renders Results screen from feedback
```

## 34. Definition of Done (overall)

The project is done when every box in §28–30 is checked, both fixture candidates (CAND-003 strong, CAND-010 weak) demonstrably receive different interview paths on the live deployment, and a judge can read `README.md` + `PROMPTS.md` + `AI_USAGE_LOG.md` and understand exactly how the system was built and why each technology was chosen.
