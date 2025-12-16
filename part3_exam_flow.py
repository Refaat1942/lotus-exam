from datetime import datetime
import time
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
QUESTION_TIME_LIMIT = 20  # seconds per question


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


# -------------------------------------------------------
# CANDIDATE FORM
# -------------------------------------------------------
def show_candidate_form():

    st.markdown("<h2>Lotus Pharmacies Placement Test</h2>", unsafe_allow_html=True)
    st.markdown("<h4>Candidate Information</h4>", unsafe_allow_html=True)

    with st.form("candidate_form"):
        name = st.text_input("Name (الاسم)")
        phone = st.text_input("Phone Number (رقم الموبايل)")
        year = st.text_input("Graduation Year (سنة التخرج)")
        uni = st.text_input("University (الجامعة)")
        exam_type = st.selectbox("Exam Type", list(SHEET_MAP.keys()))

        submitted = st.form_submit_button("Start Exam ✅")

        if submitted:
            ok, msg = validate_candidate_inputs(name, phone, year, uni, exam_type)
            if not ok:
                st.error(f"❌ {msg}")
                return

            st.session_state.user_info = {
                "name": name.strip(),
                "phone": phone.strip(),
                "year": year.strip(),
                "uni": uni.strip(),
                "exam_type": exam_type,
            }

            sheet_name = SHEET_MAP[exam_type]
            bank = load_questions_from_gsheet(QUESTIONS_SHEET_URL, sheet_name)

            selected, err = select_questions_for_exam(exam_type, bank)
            if err:
                st.error(f"❌ {err}")
                return

            st.session_state.questions = selected
            st.session_state.answers = [None] * len(selected)
            st.session_state.current_q = 0
            st.session_state.start_time = datetime.now()
            st.session_state.question_start_time = datetime.now()
            st.session_state.exam_finished = False
            st.session_state.page = "exam"

            st.rerun()


# -------------------------------------------------------
# EXAM SCREEN
# -------------------------------------------------------
def show_exam():

    questions = st.session_state.questions
    answers = st.session_state.answers
    q_index = st.session_state.current_q
    q = questions[q_index]

    # ================== TIMER ==================
    elapsed = (datetime.now() - st.session_state.question_start_time).seconds
    remaining = QUESTION_TIME_LIMIT - elapsed

    st.markdown(
        f"""
        <div style='
            font-size:22px;
            font-weight:800;
            color:#fff;
            background:#{"d9534f" if remaining <= 0 else "0b5c4a"};
            padding:10px 20px;
            border-radius:10px;
            width:240px;
            text-align:center;
            margin-bottom:15px;
        '>
            ⏱ Time left: {max(0, remaining)} sec
        </div>
        """,
        unsafe_allow_html=True
    )

    # ⛔ Time over → auto move
    if remaining <= 0:
        if answers[q_index] is None:
            answers[q_index] = -1

        time.sleep(1)

        if q_index < len(questions) - 1:
            st.session_state.current_q += 1
            st.session_state.question_start_time = datetime.now()
            st.rerun()
        else:
            finish_exam()
            return

    # ================== QUESTION ==================
    st.markdown(f"### Question {q_index + 1} of {len(questions)}")
    st.markdown(f"**{q['question']}**")

    saved_index = answers[q_index] if answers[q_index] not in (None, -1) else 0

    selected_option = st.radio(
        "Select your answer:",
        q["options"],
        index=saved_index,
        key=f"radio_q_{q_index}",
    )

    answers[q_index] = q["options"].index(selected_option)

    # ================== NAVIGATION ==================
    col1, col2, col3 = st.columns(3)

    with col2:
        if q_index < len(questions) - 1:
            if st.button("Next ➡"):
                st.session_state.current_q += 1
                st.session_state.question_start_time = datetime.now()
                st.rerun()

    with col3:
        if q_index == len(questions) - 1:
            if st.button("Submit ✅"):
                finish_exam()


# -------------------------------------------------------
# FINISH EXAM
# -------------------------------------------------------
def finish_exam():

    questions = st.session_state.questions
    answers = st.session_state.answers

    correct = 0
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
        "time_taken": time_taken,
    }

    st.session_state.exam_finished = True
    st.session_state.page = "exam"
    st.rerun()


# -------------------------------------------------------
# RESULT SCREEN
# -------------------------------------------------------
def show_exam_result():

    st.markdown("## ✅ Exam Result")

    result = st.session_state.get("result_row_dict", {})
    if not result:
        st.warning("No result data available.")
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Score %", result["score"])

    with col2:
        st.metric("Correct Answers", f"{result['correct']} / {result['total']}")

    with col3:
        st.metric("Time Taken", result["time_taken"])

    if st.button("🏠 Back to Home"):
        st.session_state.page = "home"
        st.session_state.exam_finished = False
        st.session_state.questions = []
        st.session_state.answers = []
        st.session_state.current_q = 0
        st.rerun()
