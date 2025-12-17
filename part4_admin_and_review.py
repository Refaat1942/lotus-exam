import os
import pandas as pd
from datetime import datetime
import streamlit as st


# ======================================================
# SAVE RESULT FILES
# ======================================================

def save_result_files(
    user_info,
    score,
    correct,
    total,
    time_taken,
    questions,
    answers,
):
    """
    Save exam results to Excel.
    IMPORTANT:
    - Timed Out questions (answers == -1)
      are NOT counted in score.
    - No impact on live timer or exam flow.
    """

    # =========================
    # PREPARE FOLDER
    # =========================
    os.makedirs("results", exist_ok=True)

    filename = f"{user_info['name']}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"
    filepath = os.path.join("results", filename)

    # =========================
    # SUMMARY SHEET
    # =========================
    timed_out_count = answers.count(-1)
    incorrect_count = total - correct - timed_out_count

    summary_df = pd.DataFrame([{
        "Name": user_info["name"],
        "Phone": user_info["phone"],
        "Graduation Year": user_info["year"],
        "University": user_info["uni"],
        "Exam Type": user_info["exam_type"],
        "Score %": score,
        "Correct": correct,
        "Incorrect": incorrect_count,
        "Timed Out (Not Counted)": timed_out_count,
        "Total Questions": total,
        "Time Taken": time_taken,
        "Exam Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }])

    # =========================
    # DETAILS SHEET
    # =========================
    details_rows = []

    for i, q in enumerate(questions):
        ans = answers[i]

        if ans == -1:
            candidate_answer = "No Answer"
            result = "Timed Out (Not Counted)"
            mark = "⏱"
        else:
            candidate_answer = chr(97 + ans)
            if candidate_answer == q["answer"][0]:
                result = "Correct"
                mark = "✓"
            else:
                result = "Incorrect"
                mark = "✗"

        details_rows.append({
            "Question": q["question"],
            "Candidate Answer": candidate_answer,
            "Correct Answer": q["answer"],
            "Result": result,
            "Mark": mark,
            "Category": q.get("category", ""),
            "Difficulty": q.get("difficulty", "")
        })

    details_df = pd.DataFrame(details_rows)

    # =========================
    # WRITE EXCEL FILE
    # =========================
    with pd.ExcelWriter(filepath, engine="xlsxwriter") as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        details_df.to_excel(writer, sheet_name="Details", index=False)

    return filepath


# ======================================================
# ADMIN PANEL (مطلوبة علشان app.py)
# ======================================================

def show_admin_panel():
    """
    Minimal admin panel to satisfy import in app.py
    (No logic changed, safe placeholder)
    """
    st.markdown("## Admin Panel")
    st.info("Admin panel loaded successfully.")
