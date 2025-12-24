import os
import pandas as pd
import streamlit as st
from datetime import datetime

RESULTS_FOLDER = "results"
TOKEN_FILE = "tokens.csv"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Lotus@@123"

# ================= TOKEN STATS =================
def load_token_data():
    if not os.path.exists(TOKEN_FILE):
        return pd.DataFrame()
    df = pd.read_csv(TOKEN_FILE)
    df["expires_at"] = pd.to_datetime(df["expires_at"], errors="coerce")
    return df

# ================= ADMIN PANEL =================
def show_admin_panel():

    st.markdown("## 🔐 Admin Dashboard")

    if "admin_logged" not in st.session_state:
        st.session_state.admin_logged = False

    if not st.session_state.admin_logged:
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")

        if st.button("Login"):
            if user == ADMIN_USERNAME and pw == ADMIN_PASSWORD:
                st.session_state.admin_logged = True
                st.rerun()
            else:
                st.error("Invalid credentials")
        return

    # ================= TOKEN STATISTICS =================
    st.subheader("📊 Token Statistics")

    df = load_token_data()
    if df.empty:
        st.info("No tokens generated yet.")
        return

    total = len(df)
    used = df[df["used"] == 1].shape[0]
    unused = df[df["used"] == 0].shape[0]
    expired = df[df["expires_at"] < datetime.now()].shape[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Generated", total)
    c2.metric("Used", used)
    c3.metric("Unused", unused)
    c4.metric("Expired", expired)

    st.markdown("### 👥 Tokens by HR")
    st.dataframe(
        df.groupby("generated_by").size().reset_index(name="Tokens Count"),
        use_container_width=True
    )

    st.markdown("### 📄 All Tokens")
    st.dataframe(df, use_container_width=True)

    # ================= RESULTS =================
    st.write("---")
    st.subheader("📁 Exam Results")

    rows = []
    for root, _, files in os.walk(RESULTS_FOLDER):
        for f in files:
            if f.endswith(".xlsx"):
                try:
                    d = pd.read_excel(os.path.join(root, f), sheet_name="Summary")
                    rows.append(d)
                except:
                    pass

    if rows:
        st.dataframe(pd.concat(rows, ignore_index=True), use_container_width=True)
    else:
        st.info("No exam results yet.")
