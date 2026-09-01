"""ExamCoach AI - Modern Multi-Agent Study Platform."""
from __future__ import annotations

import os
import sys
import time

# Add project root to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st

from agents.orchestrator import Orchestrator
from agents.tracker import get_user_weaknesses
from analytics.dashboard import (
    create_accuracy_trend_chart,
    create_error_distribution_chart,
    create_mastery_radar_chart,
    get_user_analytics_data,
)
from analytics.report_generator import generate_pdf_report
from core.llm_provider import PROVIDER_KEY_ENV, PROVIDER_LABELS, get_llm_provider
from db.auth import any_user_exists, authenticate, create_user
from db.database import init_db
from rag.ingestion import ingest_documents
from rag.retriever import retrieve_context

# Initialize database tables
init_db()

# Page config
st.set_page_config(
    page_title="ExamCoach AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────── CUSTOM CSS ───────────────────────────────
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  html, body, [class*="css"] { font-family: 'Outfit', sans-serif !important; }
  .stApp { background: #0a0f1e; color: #e2e8f0; }
  #MainMenu, footer, header { visibility: hidden; }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f1729 0%, #0a0f1e 100%);
    border-right: 1px solid rgba(99,102,241,0.2);
  }

  /* Glassmorphism card */
  .glass-card {
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid rgba(99,102,241,0.22);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1.25rem;
    backdrop-filter: blur(12px);
    box-shadow: 0 4px 24px rgba(0,0,0,0.25);
  }
  .glass-card:hover {
    border-color: rgba(99,102,241,0.45);
    box-shadow: 0 6px 28px rgba(99,102,241,0.12);
  }

  /* Stat card */
  .stat-card {
    background: rgba(99,102,241,0.08);
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 12px;
    padding: 1rem;
    text-align: center;
  }
  .stat-number { font-size: 2rem; font-weight: 800; color: #818cf8; }
  .stat-label  { font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }

  /* Question box */
  .question-box {
    background: linear-gradient(135deg, rgba(99,102,241,0.12), rgba(6,182,212,0.06));
    border: 1px solid rgba(99,102,241,0.35);
    border-left: 4px solid #818cf8;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin: 1rem 0;
  }

  /* Hint box */
  .hint-box {
    background: rgba(245,158,11,0.1);
    border: 1px solid rgba(245,158,11,0.35);
    border-left: 4px solid #f59e0b;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin: 0.75rem 0;
    color: #fde68a;
  }

  /* Feedback box */
  .feedback-box {
    background: rgba(16,185,129,0.08);
    border: 1px solid rgba(16,185,129,0.3);
    border-left: 4px solid #10b981;
    border-radius: 12px;
    padding: 1.25rem;
    margin: 1rem 0;
  }

  /* Tag badge */
  .tag {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(239,68,68,0.15); border: 1px solid rgba(239,68,68,0.3);
    color: #fca5a5; padding: 4px 12px; border-radius: 100px;
    font-size: 0.8rem; margin: 3px;
  }

  /* Chat */
  .chat-user {
    background: rgba(99,102,241,0.18); border: 1px solid rgba(99,102,241,0.35);
    border-radius: 12px 12px 2px 12px;
    padding: 0.75rem 1rem; margin: 0.5rem 0 0.5rem auto;
    max-width: 80%; font-size: 0.9rem;
  }
  .chat-ai {
    background: rgba(6,182,212,0.1); border: 1px solid rgba(6,182,212,0.3);
    border-radius: 12px 12px 12px 2px;
    padding: 0.75rem 1rem; margin: 0.5rem 0;
    max-width: 85%; font-size: 0.9rem;
  }

  /* Gradient text */
  .gradient-text {
    background: linear-gradient(90deg, #818cf8, #06b6d4);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }

  /* Primary Button */
  .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1, #06b6d4) !important;
    border: none !important; border-radius: 10px !important;
    font-weight: 600 !important; padding: 0.6rem 1.4rem !important;
    box-shadow: 0 4px 16px rgba(99,102,241,0.35) !important;
  }

  /* Inputs */
  input, textarea, .stTextInput input, .stTextArea textarea, .stSelectbox select {
    background: rgba(15,23,42,0.85) !important;
    border: 1px solid rgba(99,102,241,0.25) !important;
    border-radius: 10px !important; color: #e2e8f0 !important;
  }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────── SESSION STATE ───────────────────────────────
def init_session():
    defaults = {
        "user_id": None,
        "username": None,
        "active_provider": os.environ.get("EXAMCOACH_LLM_PROVIDER", "gemini"),
        "api_keys": {
            "gemini": os.environ.get("GEMINI_API_KEY", ""),
            "claude": os.environ.get("ANTHROPIC_API_KEY", ""),
            "openai": os.environ.get("OPENAI_API_KEY", ""),
        },
        "current_question": None,
        "current_topic": "",
        "current_difficulty": "Moderate (Exam Level)",
        "last_feedback": None,
        "chat_history": [],
        "hints_given": [],
        "mock_exam": None,
        "mock_answers": {},
        "mock_result": None,
        "mock_start_time": None,
    }
    # Load secrets fallback
    try:
        if not defaults["api_keys"]["gemini"] and "GEMINI_API_KEY" in st.secrets:
            defaults["api_keys"]["gemini"] = st.secrets["GEMINI_API_KEY"]
        if not defaults["api_keys"]["claude"] and "ANTHROPIC_API_KEY" in st.secrets:
            defaults["api_keys"]["claude"] = st.secrets["ANTHROPIC_API_KEY"]
        if not defaults["api_keys"]["openai"] and "OPENAI_API_KEY" in st.secrets:
            defaults["api_keys"]["openai"] = st.secrets["OPENAI_API_KEY"]
    except Exception:
        pass

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_session()


# ─────────────────────────────── AUTH SCREEN ───────────────────────────────
def render_auth_page():
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, col, c2 = st.columns([1, 1.8, 1])
    with col:
        st.markdown("""
        <div class="glass-card" style="text-align:center; padding: 2.5rem 2rem;">
            <div style="font-size: 3rem; margin-bottom: 0.25rem;">🎓</div>
            <h1 style="font-size: 2rem; font-weight: 800; margin: 0;">
                <span class="gradient-text">ExamCoach AI</span>
            </h1>
            <p style="color: #64748b; font-size: 0.95rem; margin-top: 4px;">Personalized Multi-Agent AI Study Companion</p>
        </div>
        """, unsafe_allow_html=True)

        tab_login, tab_signup = st.tabs(["🔑 Log In", "✨ New Student Sign Up"])

        with tab_login:
            with st.form("login_form"):
                u_name = st.text_input("Username", placeholder="e.g. ramsha")
                p_word = st.text_input("Password", type="password", placeholder="Enter your password")
                submitted = st.form_submit_button("Sign In →", type="primary", use_container_width=True)

                if submitted:
                    if not u_name or not p_word:
                        st.error("Please enter username and password.")
                    else:
                        user = authenticate(u_name, p_word)
                        if user:
                            st.session_state.user_id = user.id
                            st.session_state.username = user.username
                            st.success(f"Welcome back, {user.username}!")
                            st.rerun()
                        else:
                            st.error("Invalid username or password.")

        with tab_signup:
            with st.form("signup_form"):
                new_u = st.text_input("Create Username", placeholder="e.g. ramsha")
                new_p = st.text_input("Create Password", type="password", placeholder="Choose a secure password")
                submitted_reg = st.form_submit_button("Create Account & Enter →", type="primary", use_container_width=True)

                if submitted_reg:
                    if not new_u or not new_p:
                        st.error("Please fill in all fields.")
                    else:
                        try:
                            user = create_user(new_u, new_p)
                            st.session_state.user_id = user.id
                            st.session_state.username = user.username
                            st.success(f"Account created successfully for {user.username}!")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Error creating account: {exc}")


# ─────────────────────────────── MAIN DASHBOARD ───────────────────────────────
def render_main_dashboard():
    active_prov = st.session_state.active_provider
    current_key = st.session_state.api_keys.get(active_prov, "")

    # Configure Orchestrator
    orchestrator = Orchestrator(provider_name=active_prov, api_key=current_key)

    # ── Sidebar ──
    with st.sidebar:
        st.markdown(f"""
        <div style="padding: 0.5rem 0 0.25rem;">
            <div style="font-size: 1.4rem; font-weight: 800;">🎓 <span class="gradient-text">ExamCoach</span></div>
            <div style="font-size: 0.85rem; color: #64748b;">Student: <b style="color: #818cf8;">{st.session_state.username}</b></div>
        </div>
        """, unsafe_allow_html=True)
        st.divider()

        # Model Selector
        st.markdown("**🤖 AI Engine Provider**")
        chosen_prov = st.selectbox(
            "Select Provider",
            options=["gemini", "claude", "openai"],
            format_func=lambda x: PROVIDER_LABELS[x],
            index=["gemini", "claude", "openai"].index(st.session_state.active_provider),
            label_visibility="collapsed",
        )
        if chosen_prov != st.session_state.active_provider:
            st.session_state.active_provider = chosen_prov
            st.rerun()

        # Dynamic Key Input
        key_env_name = PROVIDER_KEY_ENV[chosen_prov]
        key_val = st.text_input(
            f"{PROVIDER_LABELS[chosen_prov]} Key",
            type="password",
            value=st.session_state.api_keys[chosen_prov],
            help=f"Loaded from {key_env_name} or secrets",
        )
        if key_val.strip() != st.session_state.api_keys[chosen_prov]:
            st.session_state.api_keys[chosen_prov] = key_val.strip()
            os.environ[key_env_name] = key_val.strip()
            st.rerun()

        if st.session_state.api_keys[chosen_prov]:
            st.markdown("""
            <div style="background:rgba(16,185,129,0.12);border:1px solid rgba(16,185,129,0.3);border-radius:8px;padding:6px 12px;font-size:0.8rem;color:#6ee7b7;">
                ✓ Key Active &amp; Ready
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background:rgba(245,158,11,0.12);border:1px solid rgba(245,158,11,0.3);border-radius:8px;padding:6px 12px;font-size:0.8rem;color:#fcd34d;">
                ⚠️ Enter {PROVIDER_LABELS[chosen_prov]} Key
            </div>""", unsafe_allow_html=True)

        st.divider()

        # Subject Selection
        st.markdown("**📚 Subject Area**")
        subject = st.selectbox(
            "Subject",
            ["JEE Physics", "JEE Math", "JEE Chemistry", "NEET Biology", "NEET Physics", "UPSC History", "UPSC Polity", "UPSC Economics"],
            label_visibility="collapsed",
        )

        st.divider()

        # Log out
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state.user_id = None
            st.session_state.username = None
            st.rerun()

    # ── Top Navigation Tabs ──
    tab_practice, tab_mock, tab_analytics, tab_rag = st.tabs([
        "🎯 Practice Arena",
        "⏱️ Timed Mock Test",
        "📊 Analytics & Mastery",
        "📁 Knowledge Base (RAG)",
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1: PRACTICE ARENA
    # ══════════════════════════════════════════════════════════════════════════
    with tab_practice:
        col_main, col_side = st.columns([2, 1])

        with col_side:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("### 🎯 Focus & Difficulty")

            diff_choice = st.select_slider(
                "Difficulty Tier",
                options=["Foundation", "Moderate (Exam Level)", "Challenger (Advanced)"],
                value=st.session_state.current_difficulty,
            )
            st.session_state.current_difficulty = diff_choice

            custom_topic = st.text_input("Target Topic (Optional)", placeholder="e.g. Thermodynamics, Article 32")

            st.divider()
            st.markdown("**📌 Active Weak Areas**")
            weaknesses = get_user_weaknesses(st.session_state.user_id)
            if weaknesses:
                for w in weaknesses[:6]:
                    st.markdown(f'<div class="tag">🔍 {w}</div>', unsafe_allow_html=True)
            else:
                st.caption("No weaknesses detected yet. Keep answering questions!")
            st.markdown('</div>', unsafe_allow_html=True)

        with col_main:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("### 📝 Practice Questions")

            if st.button("⚡ Generate Targeted Question", type="primary", use_container_width=True):
                with st.spinner("Formulating high-yield question..."):
                    q = orchestrator.run_practice_flow(
                        subject=subject,
                        user_id=st.session_state.user_id,
                        topic=custom_topic,
                        difficulty=diff_choice,
                    )
                    st.session_state.current_question = q
                    st.session_state.current_topic = custom_topic or subject
                    st.session_state.last_feedback = None
                    st.session_state.hints_given = []
                    st.session_state.chat_history = []

            if st.session_state.current_question:
                st.markdown(f"""
                <div class="question-box">
                    <div style="font-size:0.75rem;color:#818cf8;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:0.5rem;">
                        ❓ {subject} • {diff_choice}
                    </div>
                    <div style="font-size:1.05rem;line-height:1.7;">{st.session_state.current_question}</div>
                </div>
                """, unsafe_allow_html=True)

                # Socratic Hint Expander
                with st.expander("💡 Stuck? Request a Socratic Hint (Non-Spoiler)"):
                    hint_c1, hint_c2 = st.columns([1, 2])
                    with hint_c1:
                        hl = st.selectbox("Hint Level", [1, 2, 3], format_func=lambda x: f"Level {x}: {'Conceptual Nudge' if x==1 else 'Formulas & Setup' if x==2 else 'Solution Strategy'}")
                    with hint_c2:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("Get Hint", key="req_hint_btn"):
                            with st.spinner("Tutor crafting hint..."):
                                hint_text = orchestrator.run_hint_flow(st.session_state.current_question, hl)
                                st.session_state.hints_given.append((hl, hint_text))

                    for level, h in st.session_state.hints_given:
                        st.markdown(f"""
                        <div class="hint-box">
                            <b>💡 Hint Level {level}:</b><br/>{h}
                        </div>""", unsafe_allow_html=True)

                # Answer Submission Form
                with st.form("practice_answer_form"):
                    ans_text = st.text_area("✍️ Your step-by-step answer or selected option:", height=140, placeholder="Write your full working or reasoning...")
                    submitted = st.form_submit_button("📤 Submit for Evaluation", type="primary")

                    if submitted and ans_text.strip():
                        with st.spinner("AI Tutor evaluating step-by-step..."):
                            feedback, updated_w = orchestrator.run_evaluation_flow(
                                question=st.session_state.current_question,
                                student_answer=ans_text,
                                subject=subject,
                                user_id=st.session_state.user_id,
                                topic=st.session_state.current_topic,
                                difficulty=diff_choice,
                            )
                            st.session_state.last_feedback = feedback

            st.markdown('</div>', unsafe_allow_html=True)

            # Evaluation Feedback Box
            if st.session_state.last_feedback:
                st.markdown(f"""
                <div class="feedback-box">
                    <div style="font-size:0.8rem;color:#10b981;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:0.75rem;">📋 Evaluation &amp; Correction</div>
                    <div style="line-height:1.7;">{st.session_state.last_feedback}</div>
                </div>
                """, unsafe_allow_html=True)

                # Follow-up Chat
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.markdown("### 💬 Ask Follow-up Questions to Tutor")

                for msg in st.session_state.chat_history:
                    if msg["role"] == "user":
                        st.markdown(f'<div class="chat-user">🧑‍🎓 {msg["content"]}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="chat-ai">🤖 {msg["content"]}</div>', unsafe_allow_html=True)

                follow_up = st.chat_input("Ask a doubt regarding this explanation...")
                if follow_up:
                    st.session_state.chat_history.append({"role": "user", "content": follow_up})
                    with st.spinner("Tutor answering..."):
                        provider = get_llm_provider(name=active_prov, api_key=current_key)
                        chat_prompt = f"Question: {st.session_state.current_question}\nFeedback: {st.session_state.last_feedback}\nStudent: {follow_up}\nProvide a friendly, encouraging answer."
                        reply = provider.generate(chat_prompt, tier="fast")
                        st.session_state.chat_history.append({"role": "assistant", "content": reply})
                        st.rerun()

                st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2: TIMED MOCK TEST
    # ══════════════════════════════════════════════════════════════════════════
    with tab_mock:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### ⏱️ Timed Mock Exam with Official Scoring Schemes")
        st.caption("Simulates authentic exam conditions: JEE Main (+4 / -1), NEET-UG (+4 / -1), UPSC Mains (Subjective Rubric 0-10)")

        c_p1, c_p2, c_p3 = st.columns([1.5, 1.5, 1])
        with c_p1:
            mock_pattern = st.selectbox("Exam Pattern", ["JEE Main", "NEET-UG", "UPSC CSE"])
        with c_p2:
            mock_subj = st.selectbox("Test Subject", ["JEE Physics", "JEE Math", "NEET Biology", "UPSC Polity", "UPSC History"], key="mock_subj_select")
        with c_p3:
            st.markdown("<br>", unsafe_allow_html=True)
            start_mock = st.button("🚀 Generate & Start Test", type="primary", use_container_width=True)

        if start_mock:
            with st.spinner("Assembling exam paper with balanced difficulty..."):
                exam_data = orchestrator.run_mock_exam_generation(mock_pattern, mock_subj)
                st.session_state.mock_exam = exam_data
                st.session_state.mock_answers = {}
                st.session_state.mock_result = None
                st.session_state.mock_start_time = time.time()

        if st.session_state.mock_exam and not st.session_state.mock_result:

            @st.fragment(run_every=1)
            def _live_mock_test_fragment():
                exam = st.session_state.mock_exam
                questions = exam.get("questions", [])

                elapsed = int(time.time() - (st.session_state.mock_start_time or time.time()))
                total_sec = exam.get("time_minutes", 10) * 60
                remaining = max(0, total_sec - elapsed)

                timer_color = "#ef4444" if remaining <= 30 else "#38bdf8"
                st.markdown(f"""
                <div style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);border-radius:10px;padding:12px 18px;margin:1rem 0;display:flex;justify-content:space-between;align-items:center;">
                    <div><b>Paper:</b> {exam.get('exam_pattern')} • {exam.get('subject')} ({len(questions)} Questions)</div>
                    <div style="font-size:1.2rem;font-weight:800;color:{timer_color};">⏳ Time Remaining: {remaining // 60:02d}:{remaining % 60:02d}</div>
                </div>
                """, unsafe_allow_html=True)

                if remaining <= 0:
                    with st.spinner("⏰ Time's up — auto-submitting your test..."):
                        res = orchestrator.run_mock_exam_evaluation(
                            user_id=st.session_state.user_id,
                            exam_pattern=exam.get("exam_pattern", "JEE Main"),
                            subject=exam.get("subject", "General"),
                            questions=questions,
                            student_answers=st.session_state.mock_answers,
                            time_taken_seconds=total_sec,
                        )
                        st.session_state.mock_result = res
                    st.rerun()
                    return

                with st.form("mock_test_submission_form"):
                    for idx, q in enumerate(questions):
                        st.markdown(f"**Question {idx + 1}:**")
                        st.markdown(q["text"])

                        if mock_pattern in ["JEE Main", "NEET-UG"]:
                            ans_choice = st.radio(
                                f"Select Option for Q{idx + 1}:",
                                ["UNATTEMPTED", "A", "B", "C", "D"],
                                horizontal=True,
                                key=f"mock_radio_{idx}",
                            )
                            st.session_state.mock_answers[idx] = ans_choice
                        else:
                            ans_text = st.text_area(f"Your Answer for Q{idx + 1}:", height=120, key=f"mock_txt_{idx}")
                            st.session_state.mock_answers[idx] = ans_text

                        st.divider()

                    submit_test = st.form_submit_button("🏁 Submit Mock Test for Grading", type="primary", use_container_width=True)

                    if submit_test:
                        time_spent = int(time.time() - (st.session_state.mock_start_time or time.time()))
                        with st.spinner("Grading complete test paper..."):
                            res = orchestrator.run_mock_exam_evaluation(
                                user_id=st.session_state.user_id,
                                exam_pattern=exam.get("exam_pattern", "JEE Main"),
                                subject=exam.get("subject", "General"),
                                questions=questions,
                                student_answers=st.session_state.mock_answers,
                                time_taken_seconds=time_spent,
                            )
                            st.session_state.mock_result = res
                        st.rerun()

            _live_mock_test_fragment()

        # Display Result Scorecard
        if st.session_state.mock_result:
            res = st.session_state.mock_result
            st.markdown("### 🏆 Mock Exam Scorecard")

            r1, r2, r3, r4 = st.columns(4)
            r1.metric("Score", f"{res['score']} / {res['max_score']}")
            r2.metric("Accuracy", f"{res['accuracy']}%")
            r3.metric("Correct", res.get("correct_count", "-"))
            r4.metric("Incorrect (-ve)", res.get("incorrect_count", "-"))

            st.markdown("#### Detailed Solutions & Explanations:")
            for item in res.get("breakdown", []):
                if "q_num" in item:
                    status_color = "#10b981" if item["status"] == "Correct" else "#ef4444" if item["status"] == "Incorrect" else "#94a3b8"
                    st.markdown(f"""
                    <div style="background:rgba(15,23,42,0.8);border:1px solid rgba(99,102,241,0.25);border-radius:10px;padding:12px 16px;margin-bottom:8px;">
                        <b>Q{item['q_num']}:</b> <span style="color:{status_color};font-weight:700;">{item['status']}</span> (Marks: {item['marks']:+g}) | Your Answer: {item['student_ans']} | Correct Key: {item['correct_key']}<br/>
                        <small style="color:#94a3b8;">{item['explanation']}</small>
                    </div>""", unsafe_allow_html=True)
                elif "feedback" in item:
                    st.markdown(item["feedback"])

            if st.button("🔄 Take Another Mock Test"):
                st.session_state.mock_exam = None
                st.session_state.mock_result = None
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3: ANALYTICS & MASTERY
    # ══════════════════════════════════════════════════════════════════════════
    with tab_analytics:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### 📊 Performance Analytics & Mastery Dashboard")

        analytics_data = get_user_analytics_data(st.session_state.user_id)

        # High level KPIs
        k1, k2, k3, k4 = st.columns(4)
        k1.markdown(f"""<div class="stat-card">
            <div class="stat-number">{analytics_data['total_attempts']}</div>
            <div class="stat-label">Total Questions</div></div>""", unsafe_allow_html=True)
        k2.markdown(f"""<div class="stat-card">
            <div class="stat-number">{analytics_data['accuracy']}%</div>
            <div class="stat-label">Accuracy Rate</div></div>""", unsafe_allow_html=True)
        k3.markdown(f"""<div class="stat-card">
            <div class="stat-number">{analytics_data['avg_score']}</div>
            <div class="stat-label">Average Score (/10)</div></div>""", unsafe_allow_html=True)
        k4.markdown(f"""<div class="stat-card">
            <div class="stat-number">{len(analytics_data['mastery'])}</div>
            <div class="stat-label">Tracked Topics</div></div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Charts row
        ch1, ch2 = st.columns(2)

        with ch1:
            st.markdown("**🎯 Topic Mastery Radar Chart**")
            radar_fig = create_mastery_radar_chart(analytics_data["mastery"])
            if radar_fig:
                st.plotly_chart(radar_fig, use_container_width=True)
            else:
                st.info("Answer practice questions to plot your topic mastery polygon!")

        with ch2:
            st.markdown("**📈 Accuracy Progression Trend**")
            trend_fig = create_accuracy_trend_chart(analytics_data["attempts"])
            if trend_fig:
                st.plotly_chart(trend_fig, use_container_width=True)
            else:
                st.info("Trend lines will appear as you attempt questions!")

        # Error distribution
        err_fig = create_error_distribution_chart(analytics_data["attempts"])
        if err_fig:
            st.markdown("**⚠️ Error Classification Breakdown**")
            st.plotly_chart(err_fig, use_container_width=True)

        st.divider()

        # Download PDF Report Button
        pdf_bytes = generate_pdf_report(st.session_state.username or "Student", analytics_data)
        st.download_button(
            label="📥 Download Official PDF Progress Report",
            data=pdf_bytes,
            file_name=f"ExamCoach_Report_{st.session_state.username}.pdf",
            mime="application/pdf",
            type="primary",
        )

        st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 4: KNOWLEDGE BASE (RAG)
    # ══════════════════════════════════════════════════════════════════════════
    with tab_rag:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### 📁 Hybrid RAG Knowledge Base (PDF, Markdown, TXT)")
        st.caption("Upload your syllabus notes, standard textbooks, or PYQs. The system indexes them with FAISS vector embeddings and BM25 keywords for instant citations.")

        uploaded_files = st.file_uploader("Upload Notes", type=["pdf", "txt", "md"], accept_multiple_files=True)
        if uploaded_files:
            data_dir = "data"
            os.makedirs(data_dir, exist_ok=True)
            for f in uploaded_files:
                fpath = os.path.join(data_dir, f.name)
                with open(fpath, "wb") as dest:
                    dest.write(f.getbuffer())

            if st.button("⚡ Index & Rebuild Knowledge Store", type="primary"):
                with st.spinner("Chunking and generating embeddings..."):
                    ok = ingest_documents()
                    if ok:
                        st.success(f"Successfully indexed {len(uploaded_files)} documents into Hybrid FAISS + BM25 index!")
                    else:
                        st.error("Ingestion failed. Ensure GEMINI_API_KEY is active for embeddings.")

        st.divider()

        # Search test box
        st.markdown("**🔍 Test Retrieval Query**")
        test_q = st.text_input("Enter query to test RAG grounding:", placeholder="e.g. Fundamental Rights, Optics Snell's Law")
        if test_q:
            chunks = retrieve_context(test_q, k=3)
            if chunks:
                for c in chunks:
                    st.info(c)
            else:
                st.caption("No matching chunks found in index.")

        st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────── ROUTER ───────────────────────────────
if not st.session_state.user_id:
    render_auth_page()
else:
    render_main_dashboard()
