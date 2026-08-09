# AI Technical Evaluation Agent

An adaptive, persona-driven AI Technical Interviewer built for evaluating candidates against the 31-day AI engineering curriculum. Powered by **FastAPI**, **LangGraph**, **Gemini LLM**, **Supabase PostgreSQL**, and a **React + Vite** frontend.

🎥 **Video Demonstration**: [Watch Video Demo on Google Drive](https://drive.google.com/file/d/1UYfTWr9-VH0Kf-VOoRL8F7ukbkGxR2DU/view?usp=sharing)

---

## 🌐 Live Production & Video Links

- 🎥 **Video Demonstration**: [https://drive.google.com/file/d/1UYfTWr9-VH0Kf-VOoRL8F7ukbkGxR2DU/view?usp=sharing](https://drive.google.com/file/d/1UYfTWr9-VH0Kf-VOoRL8F7ukbkGxR2DU/view?usp=sharing)
- 🟢 **Live Frontend (Vercel)**: [https://ab-talks-hackthon-team-non-stop.vercel.app](https://ab-talks-hackthon-team-non-stop.vercel.app)
- 🟢 **Live Backend (Render)**: [https://ab-talks-hackthon-team-non-stop.onrender.com](https://ab-talks-hackthon-team-non-stop.onrender.com)
- 🟢 **Backend Health Endpoint**: [https://ab-talks-hackthon-team-non-stop.onrender.com/health](https://ab-talks-hackthon-team-non-stop.onrender.com/health)

---

## 🏗 Project Architecture

```
ai-interview-agent/
├── frontend/                     # React + Vite + Tailwind CSS v4 SPA
│   ├── src/
│   │   ├── components/           # QuestionCard, AnswerInput, FeedbackCard, ThemeToggle, etc.
│   │   ├── context/              # InterviewContext, ThemeContext
│   │   ├── pages/                # Home, Interview, Results
│   │   └── services/             # API client (with Render cold-start tolerance)
│   ├── vercel.json               # Vercel deployment & SPA routing rewrite rules
│   └── package.json
├── backend/                      # FastAPI + LangGraph + Gemini + Supabase
│   ├── app/
│   │   ├── agent/                # LangGraph nodes, router, state, fallback logic
│   │   ├── api/                  # REST endpoints (/api/interview, /report)
│   │   ├── database/             # Supabase connection & repository CRUD
│   │   ├── llm/                  # Gemini client with automatic model fallback chain
│   │   └── services/             # Interview turn orchestration & evaluation rubric
│   ├── render.yaml               # Render Web Service deployment Blueprint
│   ├── Procfile                  # Uvicorn entry point specification
│   └── requirements.txt
├── prompts/                      # System prompts (interviewer, evaluator, feedback)
├── tests/                        # Comprehensive Pytest suite (33 test cases)
├── PROMPTS.md                    # Full prompt log history
├── AI_USAGE_LOG.md               # AI development trajectory audit log
└── README.md
```

---

## 🚀 Local Development Setup

### 1. Backend Setup
```bash
cd ai-interview-agent/backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Create .env from example
cp .env.example .env
# Fill in GEMINI_API_KEY, SUPABASE_URL, and SUPABASE_SERVICE_ROLE_KEY

# Start backend dev server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd ai-interview-agent/frontend
npm install

# Create .env from example
cp .env.example .env
# Defaults to VITE_API_URL=http://localhost:8000/api

# Start frontend dev server
npm run dev
```

---

## ☁️ Production Deployment Guide

The application is architected for zero-downtime deployment using **Vercel** for the frontend and **Render** for the backend.

### STEP 1: Deploy Backend to Render
1. Create a new **Web Service** on [Render](https://render.com) connected to your GitHub repository.
2. Set Root Directory to `ai-interview-agent/backend` (or select `render.yaml` Blueprint).
3. Set the following **Environment Variables** in the Render Dashboard:
   - `GEMINI_API_KEY`: Your Google AI Studio API key
   - `SUPABASE_URL`: Your Supabase PostgreSQL project URL
   - `SUPABASE_SERVICE_ROLE_KEY`: Your Supabase service role key
   - `ALLOWED_ORIGINS`: `https://ab-talks-hackthon-team-non-stop.vercel.app,http://localhost:5173,http://localhost:3000`
4. Verify the backend deploys cleanly and the health endpoint responds at `https://ab-talks-hackthon-team-non-stop.onrender.com/health`.

### STEP 2: Deploy Frontend to Vercel
1. Import your repository into [Vercel](https://vercel.com).
2. Set Root Directory to `ai-interview-agent/frontend`. Vercel automatically detects `vercel.json` and Vite.
3. Under **Environment Variables**, set:
   - `VITE_API_URL`: `https://ab-talks-hackthon-team-non-stop.onrender.com/api`
4. Click **Deploy**. Vercel will build the frontend dist and configure SPA routing rewrites.

---

## ❄️ Render Free-Tier Cold-Start Handling

Render's free tier puts web services to sleep after 15 minutes of inactivity. When a candidate starts a new session after an idle period, the first request may take **30–50 seconds** while the Python container boots up.

- **Frontend Resilience**: The frontend API client in `src/services/api.js` avoids aggressive request timeouts and displays an active "Initiating Session..." loading spinner during cold starts rather than failing prematurely.
- **Health Check Endpoint**: `/health` is configured as the `healthCheckPath` in `render.yaml` so Render's load balancer verifies backend readiness before routing traffic.
