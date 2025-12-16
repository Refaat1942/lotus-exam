import streamlit as st
import uuid
import os
import pandas as pd
from datetime import datetime, timedelta


# ======================================================
# TOKEN CONFIG
# ======================================================
TOKEN_FILE = "tokens.csv"
APP_BASE_URL = "https://lotus-exam.streamlit.app"

EXAM_TYPES = [
    "Pharmacist (New Hire)",
    "Assistant (New Hire)",
    "Proficiency Bonus - Pharmacist",
    "Proficiency Bonus - Assistant",
    "Branch Manager Promotion",
    "Shift Manager Promotion",
]


# ======================================================
# TOKEN HELPERS
# ======================================================
def init_token_file():
    if not os.path.exists(TOKEN_FILE):
        pd.DataFrame(
            columns=["token", "exam_type", "used", "expires_at"]
        ).to_csv(TOKEN_FILE, index=False)


def generate_exam_token(exam_type, minutes_valid=30):
    init_token_file()

    token = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(minutes=minutes_valid)

    df = pd.read_csv(TOKEN_FILE)
    df.loc[len(df)] = [token, exam_type, 0, expires_at.isoformat()]
    df.to_csv(TOKEN_FILE, index=False)

    return token


# ======================================================
# HOME PAGE
# ======================================================
def show_home_page():

    # ============= SAFE CONTAINER =============
    top = st.container()
    with top:
        pass

    # ============= CSS =============
    st.markdown("""
    <style>

    .app-bg {
        background: linear-gradient(135deg, #f0f4f8, #e2ebf3);
        padding-top: 10px !important;
    }

    .main-block {
        background: white;
        border-radius: 18px;
        padding: 40px 50px;
        margin-top: 10px !important;
        box-shadow: 0 4px 14px rgba(0,0,0,0.10);
        border: 2px solid #d8e2e7;
    }

    .header-box {
        text-align: center;
        margin-bottom: 25px !important;
    }

    .title {
        font-size: 58px;
        font-weight: 900;
        color: #0b5c4a;
    }

    .subtitle {
        font-size: 24px;
        font-weight: 700;
        color: #3a3a3a;
        margin-top: -6px !important;
    }

    .btn-row {
        display: flex;
        justify-content: center;
        gap: 70px;
        margin-top: 35px !important;
    }

    .start-btn > button {
        background: linear-gradient(135deg, #0b5c4a, #0d7a5c) !important;
        color: white !important;
        padding: 25px 65px !important;
        font-size: 30px !important;
        font-weight: 900;
        border-radius: 14px;
    }

    .admin-btn > button {
        background: linear-gradient(135deg, #1f6feb, #468ff0) !important;
        color: white !important;
        padding: 25px 65px !important;
        font-size: 30px !important;
        font-weight: 900;
        border-radius: 14px;
    }

    .link-box {
        margin-top: 40px;
        padding: 25px;
        border-radius: 14px;
        background: #f7fafc;
        border: 2px dashed #0b5c4a;
    }

    </style>
    """, unsafe_allow_html=True)

    # ============= PAGE BODY =============
    st.markdown('<div class="app-bg">', unsafe_allow_html=True)
    st.markdown('<div class="main-block">', unsafe_allow_html=True)

    # ---------- HEADER ----------
    st.markdown('<div class="header-box">', unsafe_allow_html=True)
    st.image("logo.png", width=260)
    st.markdown('<div class="title">Lotus Evaluation Platform</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Your Path to Professional Assessment</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ---------- MAIN BUTTONS ----------
    st.markdown('<div class="btn-row">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        start = st.button("Start Evaluation", key="start_btn")

    with col2:
        admin = st.button("Admin Login", key="admin_btn")

    st.markdown("</div>", unsafe_allow_html=True)

    # ---------- ACTIONS ----------
    if start:
        st.session_state.page = "exam"
        st.rerun()

    if admin:
        st.session_state.page = "admin"
        st.rerun()

    # ======================================================
    # GENERATE ONE-TIME EXAM LINK (ADMIN USE)
    # ======================================================
    st.write("---")
    st.markdown("### 🔐 Generate One-Time Exam Link")

    exam_type = st.selectbox("Select Exam Type", EXAM_TYPES)
    minutes = st.number_input("Link validity (minutes)", min_value=5, max_value=180, value=30)

    if st.button("Generate Exam Link"):
        token = generate_exam_token(exam_type, minutes)
        exam_link = f"{APP_BASE_URL}?token={token}"

        st.success("✅ Exam link generated successfully")
        st.code(exam_link, language="text")
        st.info("⚠️ This link can be used **once only** and will expire automatically.")

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
