import os
import smtplib
from email.message import EmailMessage
import pandas as pd
from datetime import datetime
import streamlit as st


# ======================================================
# EMAIL CONFIG
# ======================================================

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

SENDER_EMAIL = "ahmedrefat86@gmail.com"
SENDER_PASSWORD = "pcbpuynlxfaitxfn"   # Gmail App Password
RECEIVER_EMAIL = "heba.darwish@lotuspharmacies.com"


# ======================================================
# SEND RESULT EMAIL
# ======================================================

def send_result_email(excel_path, user_info, score, timed_out_count):
    msg = EmailMessage()

    msg["Subject"] = f"📊 Online Exam Result – {user_info['name']}"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    msg.set_content(
        f"""
New Online Exam Submitted

Name: {user_info['name']}
Phone: {user_info['phone']}
University: {user_info['uni']}
Exam Type: {user_info['exam_type']}

Score: {score}%
Timed Out Questions (Not Counted): {timed_out_count}

Please find the detailed Excel result attached.
"""
    )

    with open(excel_path, "rb") as f:
        file_data = f.read()

    msg.add_attachment(
        file_data,
        maintype="application",
        subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=os.path.basename(excel_path),
    )

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)


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
    Save exam results to Excel + send email.

    - Timed Out questions (answers == -1)
      are NOT counted in score.
    - Live timer & exam flow untouched.
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

    summary_df = pd.DataFrame([
        {
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
            "Exam Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    ])

    # =========================
    # DETAILS SHEET
    # =========================
    details_rows = []

    for i, q in enumerate(questions):
        ans = answers[i]

        if ans == -1:
            details_rows.append({
                "Question": q["question"],
                "Candidate Answer": "No Answer",
                "Correct Answer": q["answer"],
                "Result": "Timed Out (Not Counted)",
                "Mark": "⏱",
                "Category": q.get("category", ""),
                "Difficulty": q.get("difficulty", ""),
            })
            continue

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
            "Difficulty": q.get("difficulty", ""),
        })

    details_df = pd.DataFrame(details_rows)

    # =========================
    # WRITE EXCEL FILE
    # =========================
    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        details_df.to_excel(writer, sheet_name="Details", index=False)

    # =========================
    # SEND EMAIL
    # =========================
    try:
        send_result_email(filepath, user_info, score, timed_out_count)
    except Exception as e:
        print("❌ Email sending failed:", e)

    return filepath


# ======================================================
# ADMIN PANEL (Required for app.py)
# ======================================================

def show_admin_panel():
    """
    Minimal admin panel placeholder.
    Safe – no logic touched.
    """
    st.markdown("## Admin Panel")
    st.info("Admin panel loaded successfully.")
