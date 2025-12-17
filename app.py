import streamlit as st

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(layout="wide")

# ======================================================
# 🔒 HIDE STREAMLIT TOOLBAR (STOP / RERUN / MENU)
# ======================================================
st.markdown("""
<style>
/* Hide top header */
header {visibility: hidden;}

/* Hide toolbar buttons (Stop / Rerun) */
[data-testid="stToolbar"] {display: none;}
[data-testid="stDecoration"] {display: none;}
[data-testid="stStatusWidget"] {display: none;}

/* Prevent right-click inspect (optional, soft protection) */
body {
    user-select: none;
}
</style>
""", unsafe_allow_html=True)

# ======================================================
# SESSION INITIALIZATION
# ======================================================
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

# ======================================================
# IMPORT PAGES
# ======================================================
from home_page import show_home_page
from part3_exam_flow import show_candidate_form, show_exam, show_exam_result
from part4_admin_and_review import show_admin_panel

# ======================================================
# PAGE ROUTING SYSTEM
# ======================================================
def main():

    # 🔐 If exam link contains token → go directly to exam
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
                show_candidate_form()   # Candidate info + Start Exam
            else:
                show_exam()             # Questions + 20 sec timer

    elif st.session_state.page == "admin":
        show_admin_panel()

# ======================================================
# RUN APP
# ======================================================
if __name__ == "__main__":
    main()
