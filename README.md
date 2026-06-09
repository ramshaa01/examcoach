# 🎓 ExamCoach

**ExamCoach** is a personalized AI study agent for competitive Indian exams like UPSC, JEE, and NEET. Built with a multi-agent orchestrated architecture, RAG grounding, and Gemini 1.5.

## 🚀 Features
- **Multi-Agent Architecture**: Separate specialized LLM personas for Question Generation, Evaluation, Knowledge Retrieval, and Weakness Tracking.
- **RAG-based Grounding**: Parses standard PDFs (NCERT, Coaching Material) via `PyMuPDF` and uses FAISS to ground agent responses in factual data.
- **Adaptive Learning**: Weaknesses are extracted and tracked across sessions to generate personalized future questions.
- **Rich UI**: Interactive Streamlit dashboard integrated with a FastAPI backbone.

## 🧠 Architecture
- **Agents Framework**: Custom orchestrator looping calls to Google Gemini API (Flash/Pro).
- **Backend / API**: FastAPI handling routing and orchestration.
- **Frontend**: Streamlit.
- **Vector Store**: FAISS (in-memory) + `models/embedding-001`.

## 🛠 Setup Instructions

1. **Clone the Repo** and navigate to the directory:
   ```bash
   cd examcoach
   ```

2. **Set your API Key**:
   ```bash
   # Windows (Powershell)
   $env:GEMINI_API_KEY="AIzaSy..."
   
   # Mac/Linux
   export GEMINI_API_KEY="AIzaSy..."
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run FastAPI Server**:
   ```bash
   # In terminal 1
   uvicorn api.main:app --reload
   ```

5. **Run Streamlit App**:
   ```bash
   # In terminal 2
   streamlit run frontend/app.py
   ```

### Enabling RAG (Optional but recommended)
1. Drop PDF files into the `data/` folder.
2. Run the ingestion script: `python -m rag.ingestion`
3. Now all Agent actions will query the FAISS index to support their outputs!

## ☁️ Deployment (Google Cloud Run)
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
