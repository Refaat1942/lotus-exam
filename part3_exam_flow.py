from datetime import datetime
import time
import os
import pandas as pd
import streamlit as st

from part1_config_and_helpers import load_questions_from_gsheet, QUESTIONS_SHEET_URL
from part2_question_selection_and_validation import (
    validate_candidate_inputs,
    select_questions_for_exam,
)
from part4_admin_and_review import save_result_files


# ======================================================
# CONFIG
# ======================================================
QUESTION_TIME_LIMIT = 45  # seconds per question
TOKEN_FILE = "tokens.csv"


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
# TOKEN HELPERS
# ======================================================
def init_token_file():
    if not os.path.exists(TOKEN_FILE):
        pd.DataFrame(
            columns=["token", "exam_type", "used", "expires_at"]
        ).to_csv(TOKEN_FILE, index=False)


def validate_token(token):
    init_token_file()
    df = pd.read_csv(TOKEN_FILE)

    row = df[df["token"] == token]
    if row.empty:
        return False, "❌ Invalid exam link"

    if int(row.iloc[0]["used"]) == 1:
        return False, "❌ This exam link was already used"

    if datetime.now() > datetime.fromisoformat(row.iloc[0]["expires_at"]):
        return False, "❌ This exam link has expired"

    return True, row.iloc[0]["exam_type"]


def mark_token_used(token):
    df = pd.read_csv(TOKEN_FILE)
    df.loc[df["token"] == token, "used"] = 1
    df.to_csv(TOKEN_FILE, index=False)


# ======================================================
# ENTRY POINT – TOKEN CHECK
# ======================================================
def handle_token_access():
    params = st.query_params
    token = params.get("token")

    if not token:
        st.error("❌ Access denied. Invalid exam link.")
        st.stop()

    if st.session_state.get("token_verified"):
        return

    ok, result = validate_token(token)
    if not ok:
        st.error(result)
        st.stop()

    mark_token_used(token)
    st.session_state.token_verified = True
    st.session_state.exam_type = result


# ======================================================
# CANDIDATE FORM
# ======================================================
def show_candidate_form():

    handle_token_access()

    st.markdown("## 📝 Candidate Information")

    with st.form("candidate_form"):
        name = st.text_input("Name")
        phone = st.text_input("Phone")
        year = st.text_input("Graduation Year")
        uni = st.text_input("University")

        submitted = st.form_submit_button("Start Exam")

        if submitted:
            ok, msg = validate_candidate_inputs(
                name, phone, year, uni, st.session_state.exam_type
            )
            if not ok:
                st.error(msg)
                return

            st.session_state.user_info = {
                "name": name,
                "phone": phone,
                "year": year,
                "uni": uni,
                "exam_type": st.session_state.exam_type,
            }

            sheet_name = SHEET_MAP[st.session_state.exam_type]
            bank = load_questions_from_gsheet(QUESTIONS_SHEET_URL, sheet_name)

            questions, err = select_questions_for_exam(
                st.session_state.exam_type, bank
            )
            if err:
                st.error(err)
                return

            st.session_state.questions = questions
            st.session_state.answers = [None] * len(questions)
            st.session_state.current_q = 0
            st.session_state.start_time = datetime.now()
            st.session_state.question_start_time = datetime.now()
            st.session_state.page = "exam"

            st.rerun()


# ======================================================
# EXAM SCREEN
# ======================================================
def show_exam():

    handle_token_access()

    questions = st.session_state.questions
    answers = st.session_state.answers
    q_index = st.session_state.current_q

    if q_index >= len(questions):
        finish_exam()
        return

    q = questions[q_index]

    elapsed = (datetime.now() - st.session_state.question_start_time).seconds
    remaining = QUESTION_TIME_LIMIT - elapsed

    st.markdown(f"### ⏱ Time left: {max(0, remaining)} sec")

    # ⏰ Time over → auto move (Timed Out)
    if remaining <= 0:
        if answers[q_index] is None:
            answers[q_index] = -1

        st.session_state.current_q += 1
        st.session_state.question_start_time = datetime.now()
        st.rerun()

    st.markdown(f"### Question {q_index + 1}")
    st.markdown(q["question"])

    # ✅ FIX: do NOT overwrite timed out answers
    if answers[q_index] in (None, -1):
        choice = st.radio("Select answer", q["options"], index=None)
    else:
        choice = st.radio("Select answer", q["options"], index=answers[q_index])

    if choice is not None:
        answers[q_index] = q["options"].index(choice)

    if st.button("Next"):
        if answers[q_index] is None:
            answers[q_index] = -1
        st.session_state.current_q += 1
        st.session_state.question_start_time = datetime.now()
        st.rerun()

    time.sleep(1)
    st.rerun()


# ======================================================
# FINISH EXAM
# ======================================================
def finish_exam():

    questions = st.session_state.questions
    answers = st.session_state.answers

    correct = 0
    timed_out_count = answers.count(-1)

    for i, q in enumerate(questions):
        if answers[i] == -1:
            continue
        if chr(97 + answers[i]) == q["answer"][0]:
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
        "timed_out": timed_out_count,
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
    st.metric("Timed Out Questions", r["timed_out"])
    st.metric("Time Taken", r["time_taken"])

    if st.button("🏠 Back to Home"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
