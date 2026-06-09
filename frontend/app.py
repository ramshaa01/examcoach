import streamlit as st
import sys
import os
import shutil

# Add project root to path so agents/rag/prompts modules are importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Config page first
st.set_page_config(page_title="ExamCoach AI", page_icon="🎓", layout="wide")

# Custom CSS for premium styling
st.markdown("""
<style>
    .reportview-container {
        background: #0F172A;
    }
    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1.2rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 10px;
    }
    .tag-container {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-top: 10px;
    }
    .tag {
        background: #ef4444;
        color: white;
        padding: 4px 10px;
        border-radius: 100px;
        font-size: 0.8rem;
        display: flex;
        align-items: center;
        gap: 5px;
    }
    .tag-clean {
        background: #10B981;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session States
if "api_key" not in st.session_state:
    api_key_val = os.environ.get("GEMINI_API_KEY", "")
    try:
        if not api_key_val and "GEMINI_API_KEY" in st.secrets:
            api_key_val = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    st.session_state.api_key = api_key_val

# Apply API key configuration if available
if st.session_state.api_key:
    os.environ["GEMINI_API_KEY"] = st.session_state.api_key
    import google.generativeai as genai
    genai.configure(api_key=st.session_state.api_key)

from agents.orchestrator import Orchestrator
from agents.tracker import load_profile, save_profile
from rag.ingestion import ingest_documents

# Initialize orchestrator
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = Orchestrator()

orchestrator = st.session_state.orchestrator

# Stats initialization
if "stats" not in st.session_state:
    st.session_state.stats = {"questions_attempted": 0, "evaluations_completed": 0, "streak": 0}

if "current_question" not in st.session_state:
    st.session_state.current_question = None

if "last_feedback" not in st.session_state:
    st.session_state.last_feedback = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Title and Banner
st.title("🎓 ExamCoach - Your Personal AI Tutor")
st.caption("A multi-agent, RAG-grounded study preparation companion for UPSC, JEE, and NEET")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    key_input = st.text_input("Gemini API Key", type="password", value=st.session_state.api_key, 
                              help="Enter your Google Gemini API key to power the agents.")
    if key_input:
        cleaned_key = key_input.strip()
        if cleaned_key != st.session_state.api_key:
            st.session_state.api_key = cleaned_key
            os.environ["GEMINI_API_KEY"] = cleaned_key
            st.rerun()

    if st.session_state.api_key:
        st.success("🔑 API Key configured successfully!")
    else:
        st.warning("⚠️ Please provide a Gemini API Key to enable the learning coach.")
    
    st.divider()
    
    # Subject selection
    st.subheader("📚 Subject Area")
    subject = st.selectbox("Choose Subject", ["JEE Physics", "JEE Math", "NEET Biology", "UPSC History", "UPSC Polity"])
    
    st.divider()

    # RAG File Upload
    st.subheader("📁 Upload Study Materials (RAG)")
    uploaded_file = st.file_uploader("Upload PDF Notes", type=["pdf"])
    if uploaded_file is not None:
        data_dir = "data"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        filepath = os.path.join(data_dir, uploaded_file.name)
        
        # Save file to data/ folder
        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        with st.spinner("Analyzing and indexing document chunks..."):
            try:
                # Set API key for embedding generation
                os.environ["GEMINI_API_KEY"] = st.session_state.api_key
                success = ingest_documents()
                if success:
                    st.success(f"Successfully indexed '{uploaded_file.name}'!")
                else:
                    st.error("Failed to index PDF.")
            except Exception as e:
                st.error(f"Error during ingestion: {e}")

    st.divider()
    
    # Stats Card
    st.subheader("📈 Practice Stats")
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Generated", st.session_state.stats["questions_attempted"])
    with col_b:
        st.metric("Evaluated", st.session_state.stats["evaluations_completed"])
        
    st.divider()

    # Reset options
    if st.button("Reset Student Profile", type="secondary"):
        save_profile({"weaknesses": []})
        st.session_state.stats = {"questions_attempted": 0, "evaluations_completed": 0, "streak": 0}
        st.session_state.current_question = None
        st.session_state.last_feedback = None
        st.session_state.chat_history = []
        st.success("Profile reset successfully!")
        st.rerun()


# Main Interface Split
col1, col2 = st.columns([2, 1])

with col2:
    st.header("🎯 Dashboard & Weaknesses")
    
    # Load and render weaknesses
    profile = load_profile()
    weaknesses = profile.get("weaknesses", [])
    
    st.subheader("Identify Areas to Improve")
    
    # Manual add weakness
    new_weak = st.text_input("Add dynamic topic to target", placeholder="e.g. Newton's laws of motion")
    if st.button("Add Topic"):
        if new_weak and new_weak not in weaknesses:
            weaknesses.append(new_weak)
            profile["weaknesses"] = weaknesses
            save_profile(profile)
            st.success(f"Added: {new_weak}")
            st.rerun()

    st.divider()
    
    st.write("**Current target weak areas:**")
    if weaknesses:
        for idx, w in enumerate(weaknesses):
            col_w, col_del = st.columns([4, 1])
            with col_w:
                st.info(f"🔍 {w}")
            with col_del:
                if st.button("❌", key=f"del_{idx}"):
                    weaknesses.remove(w)
                    profile["weaknesses"] = weaknesses
                    save_profile(profile)
                    st.rerun()
    else:
        st.success("🎉 No weaknesses identified yet! Generating questions will help discover areas of focus.")

with col1:
    st.header("📝 Practice Arena")
    
    # Error state helper
    if not st.session_state.api_key:
        st.info("💡 To start practicing, please enter a **Gemini API Key** in the sidebar on the left.")
    else:
        # Generate Question
        if st.button("Generate Practice Question", type="primary"):
            with st.spinner(f"Formulating a targeted {subject} question..."):
                try:
                    # Dynamically configure API key before running workflow
                    os.environ["GEMINI_API_KEY"] = st.session_state.api_key
                    import google.generativeai as genai
                    genai.configure(api_key=st.session_state.api_key)
                    
                    question = orchestrator.run_practice_flow(subject)
                    st.session_state.current_question = question
                    st.session_state.stats["questions_attempted"] += 1
                    # Clear previous state
                    st.session_state.last_feedback = None
                    st.session_state.chat_history = []
                except Exception as e:
                    st.error(f"Error generating question: {e}")

        # Render practice question
        if st.session_state.current_question:
            st.markdown("---")
            st.markdown("### ❓ Question")
            st.info(st.session_state.current_question)
            
            # Form submission
            with st.form("answer_form"):
                student_answer = st.text_area("Your step-by-step answer:")
                submitted = st.form_submit_button("Submit Answer for Evaluation")
                
                if submitted and student_answer:
                    with st.spinner("Analyzing your response..."):
                        try:
                            # Apply API key configuration
                            os.environ["GEMINI_API_KEY"] = st.session_state.api_key
                            import google.generativeai as genai
                            genai.configure(api_key=st.session_state.api_key)
                            
                            feedback, new_weaknesses = orchestrator.run_evaluation_flow(
                                st.session_state.current_question,
                                student_answer,
                                subject
                            )
                            st.session_state.last_feedback = feedback
                            st.session_state.stats["evaluations_completed"] += 1
                        except Exception as e:
                            st.error(f"Error during evaluation: {e}")
            
            # Show evaluation feedback and tutor follow-up
            if st.session_state.last_feedback:
                st.markdown("---")
                st.markdown("### 📋 Tutor Feedback & Solutions")
                st.success(st.session_state.last_feedback)
                
                # Conversational Coach / Chatbot for follow-up
                st.markdown("### 💬 Ask follow-up questions to your Tutor")
                
                for chat in st.session_state.chat_history:
                    if chat["role"] == "user":
                        st.chat_message("user").write(chat["content"])
                    else:
                        st.chat_message("assistant").write(chat["content"])
                
                follow_up = st.chat_input("Ask about this solution or concept...")
                if follow_up:
                    st.chat_message("user").write(follow_up)
                    st.session_state.chat_history.append({"role": "user", "content": follow_up})
                    
                    with st.spinner("Tutor is thinking..."):
                        try:
                            os.environ["GEMINI_API_KEY"] = st.session_state.api_key
                            import google.generativeai as genai
                            genai.configure(api_key=st.session_state.api_key)
                            
                            tutor_model = genai.GenerativeModel('gemini-2.5-flash')
                            chat_prompt = f"""
                            You are a friendly personal tutor assisting a student.
                            Context of the question:
                            {st.session_state.current_question}
                            
                            Your feedback and grading:
                            {st.session_state.last_feedback}
                            
                            Student's follow-up question:
                            {follow_up}
                            
                            Provide a clear, detailed, and encouraging response to their follow-up question.
                            """
                            response = tutor_model.generate_content(chat_prompt)
                            tutor_reply = response.text
                            
                            st.chat_message("assistant").write(tutor_reply)
                            st.session_state.chat_history.append({"role": "assistant", "content": tutor_reply})
                            st.rerun()
                        except Exception as e:
                            st.error(f"Tutor error: {e}")
