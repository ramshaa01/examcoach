# 🎓 ExamCoach

**ExamCoach** is a personalized AI study agent for competitive Indian exams like UPSC, JEE, and NEET. Built with a multi-agent orchestrated architecture, RAG grounding, and Gemini 1.5.

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/ramshaa01/examcoach/main/frontend/app.py)

## 🚀 Features
- **Multi-Agent Architecture**: Separate specialized LLM personas for Question Generation, Evaluation, Knowledge Retrieval, and Weakness Tracking.
- **RAG-based Grounding**: Parses standard PDFs (NCERT, Coaching Material) via `PyPDF` and uses FAISS to ground agent responses in factual data.
- **Adaptive Learning**: Weaknesses are extracted and tracked across sessions to generate personalized future questions.
- **Rich UI**: Interactive Streamlit dashboard with direct agent integration.

## 🧠 Architecture
- **Agents Framework**: Custom orchestrator looping calls to Google Gemini API (Flash/Pro).
- **Frontend**: Streamlit (calls agents directly — no separate backend needed).
- **Backend / API**: FastAPI (available for REST API usage if needed).
- **Vector Store**: FAISS (in-memory) + `models/embedding-001`.

## 🛠 Setup Instructions

1. **Clone the Repo** and navigate to the directory:
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

3. **Set your API Key**:
   ```bash
   # Windows (Powershell)
   $env:GEMINI_API_KEY="AIzaSy..."
   
   # Mac/Linux
   export GEMINI_API_KEY="AIzaSy..."
   ```

4. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the Streamlit App**:
   ```bash
   streamlit run frontend/app.py
   ```

### Running FastAPI Backend (Optional)
If you prefer using the REST API:
```bash
uvicorn api.main:app --reload
```

### Enabling RAG (Optional but recommended)
1. Drop PDF files into the `data/` folder.
2. Run the ingestion script: `python -m rag.ingestion`
3. Now all Agent actions will query the FAISS index to support their outputs!

## ☁️ Deployment

### Streamlit Community Cloud (Recommended — Free)
1. Push to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io).
3. Connect your repo, set **Main file path** to `frontend/app.py`.
4. Add `GEMINI_API_KEY` in the **Secrets** section.
5. Deploy!

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
 *(Note: For a production cloud run, it's best to split backend and frontend into two separate services. This Dockerfile uses a startup script to run both for simplicity.)*
