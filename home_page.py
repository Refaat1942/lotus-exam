import streamlit as st

def show_home_page():

    # ============================================================
    #   1) container في البداية علشان نمنع أي DIV يظهر فوق
    # ============================================================
    top = st.container()
    with top:
        pass  # مهم جدًا علشان نمنع Streamlit من وضع عناصر قبل CSS

    # ============================================================
    #   2) GLOBAL SAFE CSS (لا يمس body أو صفحة Streamlit)
    # ============================================================
    st.markdown("""
    <style>

    /* خلفية بسيطة بدون لمس Body الأساسي */
    .app-bg {
        background: linear-gradient(135deg, #f0f4f8, #e2ebf3);
        padding-top: 10px !important;
    }

    /* البوكس الداخلي فقط */
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
        margin-top: 5px !important;
        margin-bottom: 25px !important;
    }

    .title {
        font-size: 58px;
        font-weight: 900;
        color: #0b5c4a;
        margin-top: 15px !important;
    }

    .subtitle {
        font-size: 24px;
        font-weight: 700;
        color: #3a3a3a;
        margin-top: -6px !important;
    }

    .btn-row {
        display: flex;
        justify-content: center;
        gap: 70px;
        margin-top: 45px !important;
    }

    /* زرار Start Evaluation */
    .start-btn > button {
        background: linear-gradient(135deg, #0b5c4a, #0d7a5c) !important;
        color: white !important;
        padding: 25px 65px !important;
        font-size: 30px !important;
        font-weight: 900;
        border-radius: 14px;
    }

    /* زرار Admin Login */
    .admin-btn > button {
        background: linear-gradient(135deg, #1f6feb, #468ff0) !important;
        color: white !important;
        padding: 25px 65px !important;
        font-size: 30px !important;
        font-weight: 900;
        border-radius: 14px;
    }

    /* زر Back */
    .back-btn > button {
        background: #444 !important;
        color: white !important;
        padding: 18px 50px !important;
        font-size: 26px !important;
        border-radius: 12px !important;
        font-weight: 900 !important;
    }

    </style>
    """, unsafe_allow_html=True)

    # ============================================================
    #   3) نبدأ الصفحة فعليًا داخل DIV محايد بدون تلوين
    # ============================================================
    st.markdown('<div class="app-bg">', unsafe_allow_html=True)
    st.markdown('<div class="main-block">', unsafe_allow_html=True)

    # ===================== CONTENT =========================
    st.markdown('<div class="header-box">', unsafe_allow_html=True)

    # *** اللوجو ***
    st.image("logo.png", width=260)

    st.markdown('<div class="title">Lotus Evaluation Platform</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Your Path to Professional Assessment</div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # -------- Buttons --------
    st.markdown('<div class="btn-row">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        start = st.button("Start Evaluation", key="start_btn")
        st.markdown('<div class="start-btn"></div>', unsafe_allow_html=True)

    with col2:
        admin = st.button("Admin Login", key="admin_btn")
        st.markdown('<div class="admin-btn"></div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ---------------- ACTION ----------------
    if start:
        st.session_state.page = "exam"
        st.rerun()

    if admin:
        st.session_state.page = "admin"
        st.rerun()

    # ---------------- BACK BUTTON ----------------
    if st.session_state.get("page") in ["exam", "admin"]:
        st.write("---")
        back = st.button("Back to Home", key="back_home")
        st.markdown('<div class="back-btn"></div>', unsafe_allow_html=True)
        if back:
            st.session_state.page = "home"
            st.rerun()
