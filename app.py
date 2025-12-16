import streamlit as st

# ============= PAGE FULL WIDTH =============
st.set_page_config(layout="wide")

# ============= SESSION INITIALIZATION =============

def init_session():
    defaults = {
        "page": "home",
        "exam_finished": False,
        "questions": [],
        "answers": [],
        "current_q": 0,
        "result_row": {},
        "review_mode": False,
        "start_time": None,
        "result_row_dict": {},
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session()

# ============= IMPORT PAGES AFTER INITIALIZATION =============

from home_page import show_home_page
from part3_exam_flow import show_candidate_form, show_exam, show_exam_result
from part4_admin_and_review import show_admin_panel

# ============= PAGE ROUTING SYSTEM =============

def main():

    # 🔐 IMPORTANT: if exam link contains token → go directly to exam
    params = st.query_params
    if "token" in params:
        st.session_state.page = "exam"

    if st.session_state.page == "home":
        show_home_page()

    elif st.session_state.page == "exam":
        if st.session_state.exam_finished:
            show_exam_result()
        else:
            if not st.session_state.questions:
                show_candidate_form()   # بيانات + Start Exam
            else:
                show_exam()             # الأسئلة + 20 ثانية

    elif st.session_state.page == "admin":
        show_admin_panel()

# Run app
if __name__ == "__main__":
    main()
