from datetime import datetime
import streamlit as st
import streamlit.components.v1 as components

from part1_config_and_helpers import load_questions_from_gsheet, QUESTIONS_SHEET_URL
from part2_question_selection_and_validation import (
    validate_candidate_inputs,
    select_questions_for_exam,
)
from part4_admin_and_review import save_result_files


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

        exam_type = st.selectbox("Exam Type", list(SHEET_MAP.keys()), key="exam_type_form")

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

            try:
                sheet_name = SHEET_MAP[exam_type]
                bank = load_questions_from_gsheet(QUESTIONS_SHEET_URL, sheet_name)
            except Exception as e:
                st.error(f"❌ Error loading questions: {e}")
                return

            selected, err = select_questions_for_exam(exam_type, bank)
            if err:
                st.error(f"❌ {err}")
                return

            st.session_state.questions = selected
            st.session_state.answers = [None] * len(selected)
            st.session_state.current_q = 0
            st.session_state.exam_finished = False
            st.session_state.review_mode = False
            st.session_state.start_time = datetime.now()

            st.session_state.page = "exam"
            st.rerun()


# -------------------------------------------------------
#  EXAM SCREEN
# -------------------------------------------------------
def show_exam():

    questions = st.session_state.questions
    answers = st.session_state.answers
    q_index = st.session_state.current_q
    q = questions[q_index]

    # ================== TIMER ==================
    start_time = st.session_state.start_time
    elapsed = datetime.now() - start_time
    minutes, seconds = divmod(elapsed.seconds, 60)

    st.markdown(
        f"""
        <div style='
            font-size:22px;
            font-weight:700;
            color:#0b5c4a;
            background:#e3f8f3;
            padding:10px 20px;
            border-radius:10px;
            width:180px;
            text-align:center;
            margin-bottom:15px;
        '>
            ⏳ Time: {minutes:02d}:{seconds:02d}
        </div>
        """,
        unsafe_allow_html=True
    )
    # ===========================================

    st.markdown(f"### Question {q_index + 1} of {len(questions)}")
    st.markdown(f"**{q['question']}**")

    # ---------- SAFE RADIO ----------
    saved_index = answers[q_index]
    if saved_index is None:
        saved_index = 0

    selected_option = st.radio(
        "Select your answer:",
        q["options"],
        index=saved_index,
        key=f"radio_q_{q_index}",
    )

    answers[q_index] = q["options"].index(selected_option)

    # ---------- NAVIGATION ----------
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("⬅ Back", disabled=q_index == 0, key=f"back_btn_{q_index}"):
            st.session_state.current_q -= 1
            st.rerun()

    with col2:
        if q_index < len(questions) - 1:
            if st.button("Next ➡", key=f"next_btn_{q_index}"):
                st.session_state.current_q += 1
                st.rerun()

    with col3:
        if q_index == len(questions) - 1:
            if st.button("Submit ✅", key="submit_exam_btn"):
                if None in answers:
                    st.warning("⚠ Please answer all questions.")
                else:
                    finish_exam()

    if st.button("⬅ Back to Home", key="exam_to_home"):
        st.session_state.page = "home"
        st.session_state.questions = []
        st.session_state.answers = []
        st.session_state.current_q = 0
        st.rerun()


# -------------------------------------------------------
# FINISH EXAM
# -------------------------------------------------------
def finish_exam():

    questions = st.session_state.questions
    answers = st.session_state.answers

    correct = 0
    for i, q in enumerate(questions):
        correct_letter = q["answer"][0]
        user_letter = chr(97 + answers[i])
        if user_letter == correct_letter:
            correct += 1

    total = len(questions)
    score = round((correct / total) * 100, 2)
    time_taken = str(datetime.now() - st.session_state.start_time)

    user_info = st.session_state.user_info

    save_result_files(
        user_info=user_info,
        score=score,
        correct=correct,
        total=total,
        time_taken=time_taken,
        questions=questions,
        answers=answers,
    )

    st.session_state.result_row = {
        "Name": user_info["name"],
        "Phone": user_info["phone"],
        "University": user_info["uni"],
        "Exam Type": user_info["exam_type"],
        "Score": score,
        "Correct": correct,
        "Total": total,
        "Time Taken": time_taken,
        "Exam Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    st.session_state.exam_finished = True
    st.rerun()


# -------------------------------------------------------
# SHOW EXAM RESULT PAGE
# -------------------------------------------------------
def show_exam_result():

    row = st.session_state.result_row

    st.markdown("<h2>🎉 Exam Submitted Successfully</h2>", unsafe_allow_html=True)
    st.markdown(f"### Thank you, **{row.get('Name')}**")
    st.write(f"Score: **{row.get('Score')}%**")
    st.write(f"Correct: {row.get('Correct')} / {row.get('Total')}")
    st.write(f"Time taken: {row.get('Time Taken')}")
    st.write(f"Date: {row.get('Exam Date')}")

    if st.button("Review Answers 🔍", key="review_button"):
        st.session_state.review_mode = True
        st.rerun()

    if st.session_state.review_mode:
        show_review()

    if st.button("⬅ Back to Home", key="exam_result_back_home"):
        st.session_state.page = "home"
        st.session_state.exam_finished = False
        st.session_state.review_mode = False
        st.rerun()


# -------------------------------------------------------
# REVIEW ANSWERS
# -------------------------------------------------------
def show_review():

    st.markdown("## 🔍 Review Answers")

    questions = st.session_state.questions
    answers = st.session_state.answers

    for i, q in enumerate(questions):
        st.write("---")
        st.write(f"### Q{i+1}. {q['question']}")

        correct_letter = q["answer"][0]
        user_letter = chr(97 + answers[i])

        st.write(f"✔ Correct answer: **{correct_letter})**")
        if user_letter == correct_letter:
            st.success(f"Your answer: {user_letter}) ✓")
        else:
            st.error(f"Your answer: {user_letter}) ✗")

    if st.button("⬅ Back to Home", key="review_back_home"):
        st.session_state.page = "home"
        st.session_state.review_mode = False
        st.session_state.exam_finished = False
        st.rerun()
