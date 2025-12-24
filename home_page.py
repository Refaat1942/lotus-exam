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
            columns=["token", "exam_type", "used", "expires_at", "generated_by"]
        ).to_csv(TOKEN_FILE, index=False)


def generate_exam_token(exam_type, minutes_valid, generated_by):
    init_token_file()

    token = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(minutes=minutes_valid)

    df = pd.read_csv(TOKEN_FILE)
    df.loc[len(df)] = [
        token,
        exam_type,
        0,
        expires_at.isoformat(),
        generated_by
    ]
    df.to_csv(TOKEN_FILE, index=False)

    return token

# ======================================================
# HOME PAGE
# ======================================================
def show_home_page():

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

    # ======================================================
    # HR GENERATE EXAM LINK
    # ======================================================
    st.markdown("### 🔗 Generate Exam Link")

    hr_name = st.text_input("HR Name *", placeholder="Enter your name")

    exam_type = st.selectbox("Exam Type", EXAM_TYPES)
    minutes = st.number_input(
        "Link validity (minutes)", min_value=5, max_value=180, value=30
    )

    if st.button("Generate Exam Link"):
        if not hr_name.strip():
            st.warning("⚠️ Please enter your name")
            return

        token = generate_exam_token(
            exam_type=exam_type,
            minutes_valid=minutes,
            generated_by=hr_name.strip()
        )

        exam_link = f"{APP_BASE_URL}?token={token}"

        st.success("✅ Exam link generated successfully")
        st.code(exam_link, language="text")
        st.info("⚠️ This link can be used once only and will expire automatically.")

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
