import streamlit as st
import uuid
import os
import pandas as pd
from datetime import datetime, timedelta

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

# ================= TOKEN HELPERS =================
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

# ================= HOME PAGE =================
def show_home_page():

    st.markdown("## 🔗 Generate Exam Link")

    hr_name = st.text_input("HR Name *", placeholder="Enter your name")

    exam_type = st.selectbox("Exam Type", EXAM_TYPES)
    minutes = st.number_input(
        "Link validity (minutes)", min_value=5, max_value=180, value=30
    )

    if st.button("Generate Exam Link"):
        if not hr_name.strip():
            st.warning("⚠️ Please enter your name")
            return

        token = generate_exam_token(exam_type, minutes, hr_name.strip())
        exam_link = f"{APP_BASE_URL}?token={token}"

        st.success("✅ Exam link generated successfully")
        st.code(exam_link, language="text")
        st.info("This link is one-time use and expires automatically.")
