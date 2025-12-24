import streamlit as st

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(
    page_title="Lotus Evaluation Platform",
    layout="wide"
)

# ======================================================
# SESSION INIT
# ======================================================
def init_session():
    defaults = {
        "page": "home",
        "exam_finished": False,
        "questions": [],
        "answers": [],
        "current_q": 0,
        "result_row_dict": {},
        "review_mode": False,
        "start_time": None,
        "token_verified": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# ======================================================
# IMPORT PAGES
# ======================================================
from home_page import show_home_page
from part3_exam_flow import (
    show_candidate_form,
    show_exam,
    show_exam_result,
)
from part4_admin_and_review import show_admin_panel

# ======================================================
# ROUTING
# ======================================================
def main():

    params = st.query_params

    # 🔐 Admin access (hidden link)
    if "admin" in params:
        st.session_state.page = "admin"

    # 🧪 Exam access via token
    elif "token" in params:
        st.session_state.page = "exam"

    # 🏠 Default Home
    else:
        if "page" not in st.session_state:
            st.session_state.page = "home"

    # ================= PAGE SWITCH =================
    if st.session_state.page == "home":
        show_home_page()

    elif st.session_state.page == "exam":
        if st.session_state.exam_finished:
            show_exam_result()
        else:
            if not st.session_state.questions:
                show_candidate_form()
            else:
                show_exam()

    elif st.session_state.page == "admin":
        show_admin_panel()

# ======================================================
# RUN
# ======================================================
if __name__ == "__main__":
    main()
