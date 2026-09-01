# 🎓 ExamCoach

**ExamCoach** is a personalized, multi-agent AI study coach for high-stakes Indian competitive exams — JEE Main/Advanced, NEET-UG, and UPSC CSE (Polity, History, Economics).

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/ramshaa01/examcoach/main/frontend/app.py)

## 🚀 Features

- **Model-agnostic LLM layer** (`core/llm_provider.py`): switch between Google Gemini, Anthropic Claude, and OpenAI GPT-4o from the sidebar, no code changes required.
- **Adaptive difficulty**: questions scale across three tiers — Foundation, Moderate (Exam Level), Challenger (Advanced) — based on rolling per-topic mastery scores.
- **Socratic hints**: a "💡 Request Hint" flow gives progressive, non-spoiler conceptual nudges (3 levels) instead of the final answer.
- **Timed Mock Exam mode**: JEE Main and NEET-UG papers with authentic +4/-1 MCQ marking, and UPSC Mains subjective questions graded on a Structure/Content/Analysis/Conclusion rubric. Live countdown timer with auto-submit.
- **Hybrid RAG**: FAISS dense embeddings + BM25 keyword search over PDF/TXT/Markdown notes, with `[Source: file - Page N]` citation chips.
- **Analytics dashboard**: Plotly topic-mastery radar chart, accuracy trend line, and error-type breakdown, plus a downloadable PDF progress report.
- **Persistence**: SQLite (via SQLAlchemy) stores bcrypt-hashed credentials, full attempt history, and topic mastery — replacing the old flat JSON profile.

## 🧠 Architecture

- **`core/llm_provider.py`** — `LLMProvider` abstraction (Gemini / Claude / OpenAI) with `fast`/`pro` model tiers.
- **`agents/`** — one module per agent: `question_generator`, `evaluator`, `hint_agent`, `tracker` (mastery + adaptive difficulty), `mock_exam_agent`, `knowledge_agent`, and `orchestrator` tying them together.
- **`db/`** — SQLAlchemy models (`User`, `Attempt`, `TopicMastery`, `MockExamResult`) and bcrypt auth in `db/auth.py`.
- **`rag/`** — multi-format ingestion (`ingestion.py`) and hybrid FAISS+BM25 retrieval (`retriever.py`).
- **`analytics/`** — Plotly charts (`dashboard.py`) and PDF export (`report_generator.py`).
- **`frontend/app.py`** — Streamlit UI: Practice Arena, Timed Mock Test, Analytics & Mastery, and Knowledge Base tabs.
- **`api/`** — optional FastAPI backend exposing the same orchestrator flows over REST.
- **`tests/`** — pytest suite covering the LLM provider layer, DB/auth, agent parsing logic, and RAG ingestion/retrieval.

## 🛠 Setup Instructions

1. **Clone the repo** and navigate to the directory:
   ```bash
   git clone https://github.com/ramshaa01/examcoach.git
   cd examcoach
   ```

2. **Create a virtual environment** (Python 3.12 or 3.13 recommended):
   ```bash
   python -m venv .venv
   # Windows
   .\.venv\Scripts\activate
   # Mac/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set your API key(s)** — copy `.env.example` to `.env` and fill in at least one provider key (`GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, or `OPENAI_API_KEY`). You can also enter/switch keys directly from the app sidebar. `EXAMCOACH_LLM_PROVIDER` picks the default provider (`gemini` by default).

5. **Run the Streamlit app**:
   ```bash
   streamlit run frontend/app.py
   ```
   On first run you'll be asked to create a local account (username + password, bcrypt-hashed in SQLite).

6. **Run the test suite**:
   ```bash
   pytest -v
   ```

### Running the FastAPI Backend (Optional)
```bash
uvicorn api.main:app --reload
```

### Enabling RAG
1. Upload PDF/TXT/Markdown notes from the "📁 Knowledge Base (RAG)" tab, or drop files into the `data/` folder.
2. Click "⚡ Index & Rebuild Knowledge Store" (or run `python -m rag.ingestion`).
3. Practice questions, evaluations, and the tutor chat will now ground themselves in your notes, with hybrid dense+keyword search and source citations.

## ☁️ Deployment

### Streamlit Community Cloud (Recommended — Free)
1. Push to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io).
3. Connect your repo, set **Main file path** to `frontend/app.py`.
4. Add your provider API key(s) (e.g. `GEMINI_API_KEY`) in the **Secrets** section.
5. Deploy!

> Note: Streamlit Cloud's filesystem is ephemeral, so the SQLite database and FAISS/BM25 indexes reset on redeploy. For persistent multi-session data, point `EXAMCOACH_DB_PATH` at a mounted volume or external database.

### Docker / Google Cloud Run
1. Build the image:
   ```bash
   docker build -t gcr.io/YOUR_PROJECT_ID/examcoach .
   ```
2. Push to Container Registry:
   ```bash
   docker push gcr.io/YOUR_PROJECT_ID/examcoach
   ```
3. Deploy to Cloud Run:
   ```bash
   gcloud run deploy examcoach --image gcr.io/YOUR_PROJECT_ID/examcoach --platform managed --allow-unauthenticated --set-env-vars="GEMINI_API_KEY=YOUR_KEY" --port 8501
   ```
   *(For production, split backend and frontend into two separate Cloud Run services — this Dockerfile runs both for simplicity.)*
