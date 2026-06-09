import streamlit as st
import sys
import os

# Add project root to path so agents/rag/prompts modules are importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.orchestrator import Orchestrator
from agents.tracker import load_profile

# Initialize orchestrator once per session
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = Orchestrator()

orchestrator = st.session_state.orchestrator

st.set_page_config(page_title="ExamCoach AI", page_icon="🎓", layout="wide")

st.title("🎓 ExamCoach - Your Personal AI Tutor")
st.markdown("Targeting UPSC, JEE, and NEET")

# Sidebar for profile and subject selection
with st.sidebar:
    st.header("Student Dashboard")
    subject = st.selectbox("Select Subject", ["JEE Physics", "JEE Math", "NEET Biology", "UPSC History", "UPSC Polity"])
    
    st.divider()
    st.subheader("Weak Topics Tracker")
    profile = load_profile()
    weaknesses = profile.get("weaknesses", [])
    if weaknesses:
        for w in weaknesses:
            st.warning(w)
    else:
        st.success("No weak topics identified yet! Keep practicing.")

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
                question = orchestrator.run_practice_flow(subject)
                st.session_state.current_question = question
            except Exception as e:
                st.error(f"Error generating question: {e}")

    if st.session_state.current_question:
        st.info("### Question\n" + st.session_state.current_question)
        
        with st.form("answer_form"):
            student_answer = st.text_area("Your Answer:")
            submitted = st.form_submit_button("Submit Answer")
            
            if submitted and student_answer:
                with st.spinner("Evaluating your answer..."):
                    try:
                        feedback, new_weaknesses = orchestrator.run_evaluation_flow(
                            st.session_state.current_question,
                            student_answer,
                            subject
                        )
                        st.success("Evaluation Complete!")
                        st.markdown("### Feedback")
                        st.markdown(feedback)
                        st.session_state.current_question = None  # Reset after answering
                    except Exception as e:
                        st.error(f"Error during evaluation: {e}")

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
