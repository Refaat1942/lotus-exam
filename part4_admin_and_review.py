import os
import json
import pandas as pd
import streamlit as st
from datetime import datetime

# ======================================================
# CONFIG
# ======================================================
RESULTS_FOLDER = "results"
RESULTS_CSV = "results.csv"
TOKEN_FILE = "tokens.csv"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Lotus@@123"


# ======================================================
# REQUIRED FUNCTION (USED BY EXAM FLOW)
# ⚠️ DO NOT REMOVE
# ======================================================
def save_result_files(user_info, score, correct, total, time_taken, questions, answers):
    """
    This function is REQUIRED by part3_exam_flow.py
    It saves exam results safely and keeps system stable
    """

    os.makedirs(RESULTS_FOLDER, exist_ok=True)

    filename = f"{user_info['name'].replace(' ', '_')}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"
    filepath = os.path.join(RESULTS_FOLDER, filename)

    # ---------- Summary ----------
    summary_df = pd.DataFrame([{
        "Name": user_info["name"],
        "Phone": user_info["phone"],
        "University": user_info["uni"],
        "Exam Type": user_info["exam_type"],
        "Score": score,
        "Correct": correct,
        "Total": total,
        "Time Taken": time_taken,
        "Exam Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }])

    # ---------- Details ----------
    details = []
    for i, q in enumerate(questions):
        chosen_index = answers[i]
        correct_index = ord(q["answer"][0]) - 97

        details.append({
            "Question": q["question"],
            "Chosen Answer": q["options"][chosen_index],
            "Correct Answer": q["options"][correct_index],
            "Result": "Correct" if chosen_index == correct_index else "Wrong",
            "Category": q.get("category", ""),
            "Difficulty": q.get("difficulty", ""),
        })

    details_df = pd.DataFrame(details)

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        details_df.to_excel(writer, sheet_name="Details", index=False)

    # ---------- CSV LOG ----------
    row = {
        "Name": user_info["name"],
        "Phone": user_info["phone"],
        "University": user_info["uni"],
        "Exam Type": user_info["exam_type"],
        "Score": score,
        "Correct": correct,
        "Total": total,
        "Time Taken": time_taken,
        "Exam Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Excel Path": filepath,
    }

    if os.path.exists(RESULTS_CSV):
        pd.DataFrame([row]).to_csv(
            RESULTS_CSV, mode="a", header=False, index=False, encoding="utf-8"
        )
    else:
        pd.DataFrame([row]).to_csv(
            RESULTS_CSV, mode="w", header=True, index=False, encoding="utf-8"
        )

    return filepath


# ======================================================
# TOKEN DATA
# ======================================================
def load_token_data():
    if not os.path.exists(TOKEN_FILE):
        return pd.DataFrame()
    df = pd.read_csv(TOKEN_FILE)
    df["expires_at"] = pd.to_datetime(df["expires_at"], errors="coerce")
    return df


# ======================================================
# ADMIN PANEL
# ======================================================
def show_admin_panel():

    st.markdown("## 🔐 Admin Dashboard")

    if "admin_logged" not in st.session_state:
        st.session_state.admin_logged = False

    # ---------- LOGIN ----------
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

    # ==================================================
    # TOKEN STATISTICS
    # ==================================================
    st.subheader("📊 Token Statistics")

    df = load_token_data()
    if df.empty:
        st.info("No tokens generated yet.")
    else:
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
        if "generated_by" in df.columns:
            st.dataframe(
                df.groupby("generated_by").size().reset_index(name="Tokens Count"),
                use_container_width=True
            )

        st.markdown("### 📄 All Tokens")
        st.dataframe(df, use_container_width=True)

    # ==================================================
    # EXAM RESULTS
    # ==================================================
    st.write("---")
    st.subheader("📁 Exam Results")

    rows = []
    if os.path.exists(RESULTS_FOLDER):
        for f in os.listdir(RESULTS_FOLDER):
            if f.endswith(".xlsx"):
                try:
                    d = pd.read_excel(
                        os.path.join(RESULTS_FOLDER, f),
                        sheet_name="Summary"
                    )
                    rows.append(d)
                except:
                    pass

    if rows:
        st.dataframe(pd.concat(rows, ignore_index=True), use_container_width=True)
    else:
        st.info("No exam results yet.")
