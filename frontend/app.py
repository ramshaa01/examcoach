import streamlit as st
import requests
import os

API_URL = os.environ.get("API_URL", "http://localhost:8000")

st.set_page_config(page_title="ExamCoach AI", page_icon="🎓", layout="wide")

st.title("🎓 ExamCoach - Your Personal AI Tutor")
st.markdown("Targeting UPSC, JEE, and NEET")

# Sidebar for profile and subject selection
with st.sidebar:
    st.header("Student Dashboard")
    subject = st.selectbox("Select Subject", ["JEE Physics", "JEE Math", "NEET Biology", "UPSC History", "UPSC Polity"])
    
    st.divider()
    st.subheader("Weak Topics Tracker")
    try:
        profile_res = requests.get(f"{API_URL}/profile")
        if profile_res.status_code == 200:
            weaknesses = profile_res.json().get("weaknesses", [])
            if weaknesses:
                for w in weaknesses:
                    st.warning(w)
            else:
                st.success("No weak topics identified yet! Keep practicing.")
    except Exception:
        st.error("Failed to fetch profile (API might be down).")

# Session State for Question
if 'current_question' not in st.session_state:
    st.session_state.current_question = None

# Main Interface
col1, col2 = st.columns([2, 1])

with col1:
    st.header("Practice Arena")
    if st.button("Generate Practice Question", type="primary"):
        with st.spinner(f"Generating a {subject} question tailored for you..."):
            try:
                res = requests.post(f"{API_URL}/generate_question", json={"subject": subject})
                if res.status_code == 200:
                    st.session_state.current_question = res.json().get("question")
            except Exception as e:
                st.error("Error connecting to to API.")

    if st.session_state.current_question:
        st.info("### Question\n" + st.session_state.current_question)
        
        with st.form("answer_form"):
            student_answer = st.text_area("Your Answer:")
            submitted = st.form_submit_button("Submit Answer")
            
            if submitted and student_answer:
                with st.spinner("Evaluating your answer..."):
                    try:
                        eval_res = requests.post(f"{API_URL}/evaluate", json={
                            "question": st.session_state.current_question,
                            "student_answer": student_answer,
                            "subject": subject
                        })
                        if eval_res.status_code == 200:
                            data = eval_res.json()
                            st.success("Evaluation Complete!")
                            st.markdown("### Feedback")
                            st.markdown(data.get("feedback"))
                            st.session_state.current_question = None # Reset after answering
                    except Exception as e:
                        st.error("Error contacting Evaluation Agent.")

with col2:
    st.header("Instructions")
    st.markdown("""
    1. **Pick a Subject** on the left.
    2. Click **Generate Practice Question**.
    3. The Question Generator Agent will formulate a question based on your past weaknesses.
    4. Provide your working or answer.
    5. The Evaluation Agent will grade it and provide step-by-step corrections.
    6. Our Weakness Tracker Agent updates your dashboard automatically.
    """)
    st.info("Upload your notes in `data/` folder and run `python -m rag.ingestion` to enable RAG-based context parsing.")
