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
QUESTION_TIME_LIMIT = 20  # seconds per question
APPROVAL_FILE = "approvals.csv"

APP_BASE_URL = "https://lotus-exam.streamlit.app"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "ahmedrefat86@gmail.com"
SENDER_PASSWORD = "pcbpuynlxfaitxfn"  # App Password
ADMIN_EMAIL = "ahmedrefat86@gmail.com"


# ----------------------------------------
#  GOOGLE SHEETS MAPPING
# ----------------------------------------
SHEET_MAP = {
    "Pharmacist (New Hire)": "Pharmacist_New_Hire",
    "Assistant (New Hire)": "Assistant_New_Hire",
    "Proficiency Bonus - Pharmacist": "Proficiency_Bonus_Pharmacist",
    "Proficiency Bonus - Assistant": "Proficiency_Bonus_Assistant",
    "Branch Manager Promotion": "Branch_Manager_Promotion",
    "Shift Manager Promotion": "Shift_Manager_Promotion",
}


# ======================================================
# APPROVAL HELPERS
# ======================================================
def init_approval_file():
    if not os.path.exists(APPROVAL_FILE):
        pd.DataFrame(
            columns=["request_id", "name", "phone", "exam_type", "approved"]
        ).to_csv(APPROVAL_FILE, index=False)


def send_approval_email(request_id, user_info):
    approve_link = f"{APP_BASE_URL}?approve={request_id}"

    msg = EmailMessage()
    msg["Subject"] = "🟢 Exam Approval Request"
    msg["From"] = SENDER_EMAIL
    msg["To"] = ADMIN_EMAIL

    msg.set_content(f"""
New exam request:

Name: {user_info['name']}
Phone: {user_info['phone']}
Exam Type: {user_info['exam_type']}

Approve exam:
{approve_link}
""")

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)


def check_approval(request_id):
    df = pd.read_csv(APPROVAL_FILE)
    row = df[df["request_id"] == request_id]
    if row.empty:
        return False
    return int(row.iloc[0]["approved"]) == 1


def approve_request(request_id):
    df = pd.read_csv(APPROVAL_FILE)
    df.loc[df["request_id"] == request_id, "approved"] = 1
    df.to_csv(APPROVAL_FILE, index=False)


# ======================================================
# CANDIDATE FORM
# ======================================================
def show_candidate_form():

    st.markdown("## 📝 Candidate Information")

    with st.form("candidate_form"):
        name = st.text_input("Name")
        phone = st.text_input("Phone Number")
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

            user_info = {
                "name": name.strip(),
                "phone": phone.strip(),
                "year": year.strip(),
                "uni": uni.strip(),
                "exam_type": exam_type,
            }

            df = pd.read_csv(APPROVAL_FILE)
            df.loc[len(df)] = [request_id, name, phone, exam_type, 0]
            df.to_csv(APPROVAL_FILE, index=False)

            send_approval_email(request_id, user_info)

            st.session_state.user_info = user_info
            st.session_state.request_id = request_id
            st.session_state.waiting_approval = True

            st.success("✅ Request sent. Waiting for approval...")
            st.rerun()


# ======================================================
# WAITING FOR APPROVAL SCREEN
# ======================================================
def show_waiting_for_approval():

    st.info("⏳ Waiting for admin approval...")

    time.sleep(3)

    if check_approval(st.session_state.request_id):

        exam_type = st.session_state.user_info["exam_type"]
        sheet_name = SHEET_MAP[exam_type]
        bank = load_questions_from_gsheet(QUESTIONS_SHEET_URL, sheet_name)

        selected, err = select_questions_for_exam(exam_type, bank)
        if err:
            st.error(err)
            return

        st.session_state.questions = selected
        st.session_state.answers = [None] * len(selected)
        st.session_state.current_q = 0
        st.session_state.start_time = datetime.now()
        st.session_state.question_start_time = datetime.now()
        st.session_state.exam_finished = False
        st.session_state.waiting_approval = False
        st.session_state.page = "exam"

        st.rerun()

    st.rerun()


# ======================================================
# EXAM SCREEN
# ======================================================
def show_exam():

    # Handle approval link
    params = st.query_params
    approve_id = params.get("approve")
    if approve_id:
        init_approval_file()
        approve_request(approve_id)
        st.success("✅ Exam approved successfully.")
        st.stop()

    if st.session_state.get("waiting_approval"):
        show_waiting_for_approval()
        return

    questions = st.session_state.questions
    answers = st.session_state.answers
    q_index = st.session_state.current_q
    q = questions[q_index]

    elapsed = (datetime.now() - st.session_state.question_start_time).seconds
    remaining = QUESTION_TIME_LIMIT - elapsed

    st.markdown(f"### ⏱ Time left: {max(0, remaining)} sec")

    if remaining <= 0:
        if answers[q_index] is None:
            answers[q_index] = -1

        if q_index < len(questions) - 1:
            st.session_state.current_q += 1
            st.session_state.question_start_time = datetime.now()
            st.rerun()
        else:
            finish_exam()
            return

    st.markdown(f"### Question {q_index + 1}")
    st.markdown(q["question"])

    saved_index = answers[q_index] if answers[q_index] not in (None, -1) else 0
    choice = st.radio("Select answer", q["options"], index=saved_index)
    answers[q_index] = q["options"].index(choice)

    if st.button("Next ➡"):
        st.session_state.current_q += 1
        st.session_state.question_start_time = datetime.now()
        st.rerun()


# ======================================================
# FINISH EXAM
# ======================================================
def finish_exam():

    questions = st.session_state.questions
    answers = st.session_state.answers

    correct = 0
    for i, q in enumerate(questions):
        if answers[i] != -1 and chr(97 + answers[i]) == q["answer"][0]:
            correct += 1

    total = len(questions)
    score = round((correct / total) * 100, 2)
    time_taken = str(datetime.now() - st.session_state.start_time)

    save_result_files(
        user_info=st.session_state.user_info,
        score=score,
        correct=correct,
        total=total,
        time_taken=time_taken,
        questions=questions,
        answers=answers,
    )

    st.session_state.result_row_dict = {
        "score": score,
        "correct": correct,
        "total": total,
        "time_taken": time_taken,
    }

    st.session_state.exam_finished = True
    st.rerun()


# ======================================================
# RESULT SCREEN
# ======================================================
def show_exam_result():

    r = st.session_state.result_row_dict

    st.success("✅ Exam Completed")
    st.metric("Score %", r["score"])
    st.metric("Correct", f"{r['correct']} / {r['total']}")
    st.metric("Time Taken", r["time_taken"])

    if st.button("🏠 Back to Home"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
