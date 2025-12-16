from datetime import datetime
import time
import uuid
import os
import pandas as pd
import streamlit as st
import smtplib
from email.message import EmailMessage

from part1_config_and_helpers import load_questions_from_gsheet, QUESTIONS_SHEET_URL
from part2_question_selection_and_validation import (
    validate_candidate_inputs,
    select_questions_for_exam,
)
from part4_admin_and_review import save_result_files


# ======================================================
# CONFIG
# ======================================================
QUESTION_TIME_LIMIT = 20
APPROVAL_FILE = "approvals.csv"

APP_BASE_URL = "https://lotus-exam.streamlit.app"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "ahmedrefat86@gmail.com"
SENDER_PASSWORD = "pcbpuynlxfaitxfn"   # Gmail App Password
ADMIN_EMAIL = "ahmedrefat86@gmail.com"


# ======================================================
# EXAM TYPES
# ======================================================
SHEET_MAP = {
    "Pharmacist (New Hire)": "Pharmacist_New_Hire",
    "Assistant (New Hire)": "Assistant_New_Hire",
    "Proficiency Bonus - Pharmacist": "Proficiency_Bonus_Pharmacist",
    "Proficiency Bonus - Assistant": "Proficiency_Bonus_Assistant",
    "Branch Manager Promotion": "Branch_Manager_Promotion",
    "Shift Manager Promotion": "Shift_Manager_Promotion",
}


# ======================================================
# APPROVAL STORAGE
# ======================================================
def init_approval_file():
    if not os.path.exists(APPROVAL_FILE):
        pd.DataFrame(
            columns=["request_id", "name", "phone", "exam_type", "status"]
        ).to_csv(APPROVAL_FILE, index=False)


def approve_request(request_id):
    df = pd.read_csv(APPROVAL_FILE)
    df.loc[df["request_id"] == request_id, "status"] = "approved"
    df.to_csv(APPROVAL_FILE, index=False)


def reject_request(request_id):
    df = pd.read_csv(APPROVAL_FILE)
    df.loc[df["request_id"] == request_id, "status"] = "rejected"
    df.to_csv(APPROVAL_FILE, index=False)


def get_request_status(request_id):
    df = pd.read_csv(APPROVAL_FILE)
    row = df[df["request_id"] == request_id]
    if row.empty:
        return "pending"
    return row.iloc[0]["status"]


# ======================================================
# EMAIL (HTML APPROVE / REJECT)
# ======================================================
def send_approval_email(request_id, user_info):
    approve_link = f"{APP_BASE_URL}?approve={request_id}"
    reject_link = f"{APP_BASE_URL}?reject={request_id}"

    msg = EmailMessage()
    msg["Subject"] = "🟢 Exam Approval Request"
    msg["From"] = SENDER_EMAIL
    msg["To"] = ADMIN_EMAIL

    msg.set_content("HTML email required")

    msg.add_alternative(f"""
    <html>
    <body style="font-family:Arial">
        <h3>New Exam Request</h3>
        <p><b>Name:</b> {user_info['name']}</p>
        <p><b>Phone:</b> {user_info['phone']}</p>
        <p><b>Exam Type:</b> {user_info['exam_type']}</p>
        <br>
        <a href="{approve_link}"
           style="padding:12px 20px;background:#28a745;color:#fff;
           text-decoration:none;border-radius:6px;font-weight:bold;">
           ✅ Approve
        </a>
        &nbsp;&nbsp;
        <a href="{reject_link}"
           style="padding:12px 20px;background:#dc3545;color:#fff;
           text-decoration:none;border-radius:6px;font-weight:bold;">
           ❌ Reject
        </a>
        <br><br>
        <small>This decision page is admin-only.</small>
    </body>
    </html>
    """, subtype="html")

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)


# ======================================================
# ADMIN APPROVAL PAGE (BLOCK EXAM)
# ======================================================
def handle_admin_action():
    params = st.query_params
    approve_id = params.get("approve")
    reject_id = params.get("reject")

    if approve_id or reject_id:
        init_approval_file()

        st.markdown("## 🔐 Admin Decision")

        if approve_id:
            approve_request(approve_id)
            st.success("✅ Exam approved successfully.")

        if reject_id:
            reject_request(reject_id)
            st.error("❌ Exam request rejected.")

        st.info("You can safely close this page now.")
        st.stop()   # ⛔ STOP ANY EXAM FLOW


# ======================================================
# CANDIDATE FORM
# ======================================================
def show_candidate_form():

    st.markdown("## 📝 Candidate Information")

    with st.form("candidate_form"):
        name = st.text_input("Name")
        phone = st.text_input("Phone")
        year = st.text_input("Graduation Year")
        uni = st.text_input("University")
        exam_type = st.selectbox("Exam Type", list(SHEET_MAP.keys()))

        submitted = st.form_submit_button("Start Exam")

        if submitted:
            ok, msg = validate_candidate_inputs(name, phone, year, uni, exam_type)
            if not ok:
                st.error(msg)
                return

            init_approval_file()
            request_id = str(uuid.uuid4())

            df = pd.read_csv(APPROVAL_FILE)
            df.loc[len(df)] = [request_id, name, phone, exam_type, "pending"]
            df.to_csv(APPROVAL_FILE, index=False)

            user_info = {
                "name": name,
                "phone": phone,
                "year": year,
                "uni": uni,
                "exam_type": exam_type,
            }

            send_approval_email(request_id, user_info)

            st.session_state.user_info = user_info
            st.session_state.request_id = request_id
            st.session_state.waiting_approval = True

            st.success("⏳ Request sent. Waiting for admin approval...")
            st.rerun()


# ======================================================
# WAITING SCREEN
# ======================================================
def show_waiting_for_approval():

    st.info("⏳ Waiting for admin approval...")
    time.sleep(3)

    status = get_request_status(st.session_state.request_id)

    if status == "approved":
        exam_type = st.session_state.user_info["exam_type"]
        sheet_name = SHEET_MAP[exam_type]
        bank = load_questions_from_gsheet(QUESTIONS_SHEET_URL, sheet_name)

        questions, err = select_questions_for_exam(exam_type, bank)
        if err:
            st.error(err)
            return

        st.session_state.questions = questions
        st.session_state.answers = [None] * len(questions)
        st.session_state.current_q = 0
        st.session_state.start_time = datetime.now()
        st.session_state.question_start_time = datetime.now()
        st.session_state.waiting_approval = False
        st.session_state.page = "exam"

        st.rerun()

    if status == "rejected":
        st.error("❌ Your exam request was rejected.")
        st.stop()

    st.rerun()


# ======================================================
# EXAM SCREEN
# ======================================================
def show_exam():

    handle_admin_action()  # ⬅️ IMPORTANT

    if st.session_state.get("waiting_approval"):
        show_waiting_for_approval()
        return

    q = st.session_state.questions[st.session_state.current_q]
    idx = st.session_state.current_q

    elapsed = (datetime.now() - st.session_state.question_start_time).seconds
    remaining = QUESTION_TIME_LIMIT - elapsed

    st.markdown(f"### ⏱ Time left: {max(0, remaining)} sec")
    st.markdown(q["question"])

    choice = st.radio(
        "Select answer",
        q["options"],
        index=0,
        key=f"q_{idx}"
    )

    st.session_state.answers[idx] = q["options"].index(choice)

    if st.button("Next"):
        st.session_state.current_q += 1
        st.session_state.question_start_time = datetime.now()
        st.rerun()


# ======================================================
# FINISH EXAM
# ======================================================
def finish_exam():
    st.success("Exam Finished")
