import streamlit as st
import sys
import os
import time

# Add project root to path so agents/rag/prompts modules are importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Config page first
st.set_page_config(page_title="ExamCoach AI - Premium Tutor", page_icon="🎓", layout="wide")

# Custom CSS for premium styling, custom fonts, glassmorphism, animations, and bubbles
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">

<style>
    /* Global styling and Font */
    html, body, [class*="css"], .stMarkdown {
        font-family: 'Outfit', sans-serif !important;
    }
    
    /* Main container background gradient */
    .stApp {
        background: radial-gradient(circle at 50% 50%, #0F172A 0%, #020617 100%) !important;
    }
    
    /* Glassmorphic Cards */
    .glass-card {
        background: rgba(30, 41, 59, 0.45) !important;
        backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        margin-bottom: 1.25rem !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
    }
    
    /* Stats glow metrics */
    .stat-glow {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(6, 182, 212, 0.15) 100%) !important;
        border: 1px solid rgba(99, 102, 241, 0.25) !important;
        box-shadow: 0 0 15px rgba(99, 102, 241, 0.1) !important;
    }
    
    /* Glowing Title Headers */
    .glow-text {
        background: linear-gradient(90deg, #38BDF8 0%, #818CF8 50%, #C084FC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }

    /* Buttons visual improvements */
    .stButton>button {
        background: linear-gradient(90deg, #6366F1 0%, #4F46E5 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4) !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.6) !important;
        background: linear-gradient(90deg, #4F46E5 0%, #4338CA 100%) !important;
    }

    /* Chat bubble design */
    .chat-bubble {
        padding: 12px 16px;
        border-radius: 16px;
        margin-bottom: 10px;
        max-width: 85%;
        line-height: 1.5;
        font-size: 0.95rem;
        animation: slideUp 0.35s ease;
    }
    .chat-user {
        background: #4F46E5;
        color: white;
        margin-left: auto;
        border-bottom-right-radius: 4px;
        box-shadow: 0 4px 10px rgba(79, 70, 229, 0.25);
    }
    .chat-assistant {
        background: rgba(30, 41, 59, 0.8);
        color: #E2E8F0;
        border-bottom-left-radius: 4px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
    }
    
    /* Animations */
    @keyframes slideUp {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .animate-slide {
        animation: slideUp 0.5s ease-out;
    }
</style>
""", unsafe_allow_html=True)

# Authentication state management
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# ----------------- LOGIN PAGE -----------------
if not st.session_state.logged_in:
    # Outer centering layout
    _, col_center, _ = st.columns([1.2, 1.6, 1.2])
    
    with col_center:
        st.write("")
        st.write("")
        st.write("")
        st.markdown("""
        <div style='text-align: center; margin-bottom: 2rem;'>
            <h1 class='glow-text' style='font-size: 3rem; margin-bottom: 0px;'>🎓 ExamCoach AI</h1>
            <p style='color: #94A3B8; font-size: 1.1rem;'>Your personal orchestrated study tutor</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("🔑 Student Authentication")
        st.caption("Sign in to load your personalized dashboard.")
        
        user_input = st.text_input("Student Name", placeholder="e.g. Ramshaa")
        pass_input = st.text_input("Passcode", type="password", placeholder="Enter your exam passcode")
        
        st.info("💡 Demo Credentials: Name = `Ramshaa`, Passcode = `exam2026`")
        
        if st.button("Enter Dashboard"):
            if user_input.strip() == "Ramshaa" and pass_input == "exam2026":
                st.session_state.logged_in = True
                st.session_state.username = user_input.strip()
                st.success("Access Granted! Loading your study arena...")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Invalid student name or passcode. Please try again.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ----------------- MAIN APP PAGE -----------------

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

# Header Banner with user welcome
st.markdown(f"""
<div style='display: flex; justify-content: space-between; align-items: center; padding: 1rem 0; margin-bottom: 2rem; border-bottom: 1px solid rgba(255, 255, 255, 0.08);'>
    <div>
        <h1 class='glow-text' style='margin: 0; font-size: 2.2rem;'>🎓 ExamCoach AI</h1>
        <p style='color: #64748B; margin: 0; font-size: 0.95rem;'>Targeting UPSC, JEE, and NEET preparation</p>
    </div>
    <div style='background: rgba(99, 102, 241, 0.1); border: 1px solid rgba(99, 102, 241, 0.3); padding: 6px 16px; border-radius: 20px; font-weight: 500;'>
        👤 Student: <span style='color: #818CF8;'>{st.session_state.username}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("<h3>⚙️ Control Dashboard</h3>", unsafe_allow_html=True)
    
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
    
    st.subheader("📚 Target Exam & Subject")
    subject = st.selectbox("Select Subject", ["JEE Physics", "JEE Math", "NEET Biology", "UPSC History", "UPSC Polity"])
    
    st.divider()

    st.subheader("📁 Study Materials (RAG)")
    uploaded_file = st.file_uploader("Upload Notes PDF", type=["pdf"])
    if uploaded_file is not None:
        data_dir = "data"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        filepath = os.path.join(data_dir, uploaded_file.name)
        
        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        with st.spinner("Analyzing notes and updating vector store..."):
            try:
                os.environ["GEMINI_API_KEY"] = st.session_state.api_key
                success = ingest_documents()
                if success:
                    st.success(f"Indexed '{uploaded_file.name}'!")
                else:
                    st.error("Failed to build index.")
            except Exception as e:
                st.error(f"Ingestion error: {e}")

    st.divider()
    
    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()


# Main Interface Split
col1, col2 = st.columns([2, 1])

with col2:
    # Stats indicator
    st.markdown("<div class='glass-card stat-glow'>", unsafe_allow_html=True)
    st.subheader("📈 Performance Metrics")
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Total Practiced", st.session_state.stats["questions_attempted"])
    with col_b:
        st.metric("Total Evaluated", st.session_state.stats["evaluations_completed"])
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Weakness dashboard panel
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("🎯 Active Weak Areas")
    
    profile = load_profile()
    weaknesses = profile.get("weaknesses", [])
    
    new_weak = st.text_input("Add dynamic topic to target", placeholder="e.g. Circular Motion", key="add_weakness")
    if st.button("Add Target Topic", use_container_width=True):
        if new_weak.strip() and new_weak.strip() not in weaknesses:
            weaknesses.append(new_weak.strip())
            profile["weaknesses"] = weaknesses
            save_profile(profile)
            st.success(f"Added target: {new_weak}")
            st.rerun()

    st.divider()
    
    if weaknesses:
        for idx, w in enumerate(weaknesses):
            col_w, col_del = st.columns([4, 1])
            with col_w:
                st.markdown(f"<div style='background: rgba(239, 68, 68, 0.1); color: #FCA5A5; border: 1px solid rgba(239, 68, 68, 0.2); padding: 8px 12px; border-radius: 8px; font-weight: 500; font-size: 0.9rem;'>🔍 {w}</div>", unsafe_allow_html=True)
            with col_del:
                if st.button("❌", key=f"del_{idx}"):
                    weaknesses.remove(w)
                    profile["weaknesses"] = weaknesses
                    save_profile(profile)
                    st.rerun()
    else:
        st.markdown("<div style='color: #10B981; font-weight: 500; font-size: 0.95rem;'>🎉 No weaknesses identified yet!</div>", unsafe_allow_html=True)
    
    if st.button("Reset Stats & Profile", type="secondary", use_container_width=True):
        save_profile({"weaknesses": []})
        st.session_state.stats = {"questions_attempted": 0, "evaluations_completed": 0, "streak": 0}
        st.session_state.current_question = None
        st.session_state.last_feedback = None
        st.session_state.chat_history = []
        st.success("Profile reset successfully!")
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with col1:
    st.markdown("<div class='glass-card animate-slide'>", unsafe_allow_html=True)
    st.subheader("📝 Practice Arena")
    
    if not st.session_state.api_key:
        st.info("💡 To start practicing, please enter a valid **Gemini API Key** in the sidebar on the left.")
    else:
        # Generate Question button
        if st.button("Generate Practice Question", type="primary", use_container_width=True):
            with st.spinner(f"Formulating a targeted {subject} question..."):
                try:
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
        
        # Render current question
        if st.session_state.current_question:
            st.markdown("---")
            st.markdown("### ❓ Current Question")
            
            # Check if it was an error or a question
            if st.session_state.current_question.startswith("Error"):
                st.error(st.session_state.current_question)
            else:
                st.info(st.session_state.current_question)
                
                # Answer form
                with st.form("answer_form"):
                    student_answer = st.text_area("Your step-by-step answer:", placeholder="Write your working out, formulas, or explanation...")
                    submitted = st.form_submit_button("Submit Answer for Evaluation")
                    
                    if submitted and student_answer:
                        with st.spinner("Analyzing and evaluating..."):
                            try:
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
    st.markdown("</div>", unsafe_allow_html=True)

    # Feedback and chat block
    if st.session_state.last_feedback:
        st.markdown("<div class='glass-card animate-slide'>", unsafe_allow_html=True)
        st.markdown("### 📋 Tutor Evaluation Feedback")
        if st.session_state.last_feedback.startswith("Error"):
            st.error(st.session_state.last_feedback)
        else:
            st.success(st.session_state.last_feedback)
        
        st.markdown("---")
        st.markdown("### 💬 Chat with your Personal Tutor")
        
        # Render bubbles
        for chat in st.session_state.chat_history:
            bubble_class = "chat-user" if chat["role"] == "user" else "chat-assistant"
            st.markdown(f"""
            <div class="chat-bubble {bubble_class}">
                <b>{'You' if chat['role'] == 'user' else 'Tutor'}:</b><br>{chat['content']}
            </div>
            """, unsafe_allow_html=True)
        
        follow_up = st.chat_input("Ask about this solution or concept...")
        if follow_up:
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
                    
                    st.session_state.chat_history.append({"role": "assistant", "content": tutor_reply})
                    st.rerun()
                except Exception as e:
                    st.error(f"Tutor error: {e}")
        st.markdown("</div>", unsafe_allow_html=True)
