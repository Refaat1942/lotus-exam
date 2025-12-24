import os
import json
from datetime import datetime
import pandas as pd
import streamlit as st

RESULTS_FOLDER = "results"
RESULTS_CSV = "results.csv"
ADMIN_PASSWORD = "Lotus@@123"
TOKEN_FILE = "tokens.csv"


# ============================================================
# SAVE RESULT TO EXCEL
# ============================================================

def save_result_excel(user_info, score, correct, total, time_taken, questions, answers):

    exam_type = user_info.get("exam_type", "Exam")
    folder_path = os.path.join(RESULTS_FOLDER, exam_type.replace(" ", "_"))
    os.makedirs(folder_path, exist_ok=True)

    filename = f"{user_info.get('name').replace(' ', '_')}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"
    filepath = os.path.join(folder_path, filename)

    summary_df = pd.DataFrame([{
        "Name": user_info.get("name"),
        "Phone": user_info.get("phone"),
        "Graduation Year": user_info.get("year"),
        "University": user_info.get("uni"),
        "Exam Type": exam_type,
        "Score": f"{score:.0f}%",
        "Correct": correct,
        "Total": total,
        "Time Taken": time_taken,
        "Exam Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }])

    details = []
    for i, q in enumerate(questions):
        chosen_index = answers[i]
        chosen_full = q["options"][chosen_index]

        correct_letter = q["answer"][0]
        correct_index = ord(correct_letter) - 97
        correct_full = q["options"][correct_index]

        result = "Correct" if chosen_index == correct_index else "Wrong"

        details.append({
            "Question": q["question"],
            "Chosen Answer": chosen_full,
            "Correct Answer": correct_full,
            "Result": result,
            "Category": q["category"],
            "Difficulty": q["difficulty"],
        })

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        pd.DataFrame(details).to_excel(writer, sheet_name="Details", index=False)

    return filepath


# ============================================================
# SAVE RESULT FILES (Excel + CSV)
# ============================================================

def save_result_files(user_info, score, correct, total, time_taken, questions, answers):

    filepath = save_result_excel(
        user_info, score, correct, total, time_taken, questions, answers
    )

    row = {
        "Name": user_info["name"],
        "Phone": user_info["phone"],
        "Graduation Year": user_info["year"],
        "University": user_info["uni"],
        "Exam Type": user_info["exam_type"],
        "Score": score,
        "Correct": correct,
        "Total": total,
        "Time Taken": time_taken,
        "Exam Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Answers": json.dumps(answers, ensure_ascii=False),
        "Questions": json.dumps(questions, ensure_ascii=False),
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

    return row


# ============================================================
# LOAD RESULTS
# ============================================================

def load_results():
    if not os.path.exists(RESULTS_CSV):
        return pd.DataFrame()
    return pd.read_csv(RESULTS_CSV, on_bad_lines="skip")


# ============================================================
# TOKEN STATISTICS
# ============================================================

def load_token_stats():
    if not os.path.exists(TOKEN_FILE):
        return None

    df = pd.read_csv(TOKEN_FILE)
    df["expires_at"] = pd.to_datetime(df["expires_at"], errors="coerce")

    total = len(df)
    used = df[df["used"] == 1].shape[0]
    unused = df[df["used"] == 0].shape[0]
    expired = df[df["expires_at"] < datetime.now()].shape[0]

    return {
        "total": total,
        "used": used,
        "unused": unused,
        "expired": expired,
        "by_exam": df.groupby("exam_type").size().reset_index(name="count")
    }


# ============================================================
# ADMIN PANEL
# ============================================================

def show_admin_panel():

    st.markdown("## 🔐 Admin Panel")

    if "admin_logged" not in st.session_state:
        st.session_state.admin_logged = False

    if not st.session_state.admin_logged:
        pw = st.text_input("Admin Password", type="password")
        if st.button("Login"):
            if pw == ADMIN_PASSWORD:
                st.session_state.admin_logged = True
                st.rerun()
            else:
                st.error("Wrong password")
        return

    # ================== TOKEN STATS ==================
    st.subheader("📊 Exam Links Statistics")

    stats = load_token_stats()
    if stats:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Generated Links", stats["total"])
        c2.metric("Used Links", stats["used"])
        c3.metric("Unused Links", stats["unused"])
        c4.metric("Expired Links", stats["expired"])

        st.markdown("### By Exam Type")
        st.dataframe(stats["by_exam"], use_container_width=True)
    else:
        st.info("No tokens generated yet.")

    st.write("---")

    # ================== RESULTS TABLE ==================
    st.subheader("📁 Exam Results")

    rows = []
    for root, _, files in os.walk(RESULTS_FOLDER):
        for f in files:
            if f.endswith(".xlsx"):
                path = os.path.join(root, f)
                try:
                    df = pd.read_excel(path, sheet_name="Summary")
                    df["Excel Path"] = path
                    rows.append(df)
                except:
                    pass

    if not rows:
        st.warning("No results found.")
        return

    df = pd.concat(rows, ignore_index=True)
    df["Exam Date"] = pd.to_datetime(df["Exam Date"], errors="coerce")
    df = df.sort_values("Exam Date", ascending=False)

    st.dataframe(
        df[
            [
                "Name",
                "Phone",
                "University",
                "Score",
                "Correct",
                "Total",
                "Time Taken",
                "Exam Type",
                "Exam Date",
                "Excel Path",
            ]
        ],
        use_container_width=True,
        height=500,
    )
