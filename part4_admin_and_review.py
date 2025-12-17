import os
import smtplib
from email.message import EmailMessage
import pandas as pd
from datetime import datetime
import streamlit as st


SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

SENDER_EMAIL = "ahmedrefat86@gmail.com"
SENDER_PASSWORD = "pcbpuynlxfaitxfn"
RECEIVER_EMAIL = "heba.darwish@lotuspharmacies.com"


def send_result_email(excel_path, user_info, score, timed_out_count):
    msg = EmailMessage()
    msg["Subject"] = f"📊 Online Exam Result – {user_info['name']}"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    msg.set_content(
        f"""
Name: {user_info['name']}
Phone: {user_info['phone']}
Exam Type: {user_info['exam_type']}

Score: {score}%
Timed Out Questions (Not Counted): {timed_out_count}
"""
    )

    with open(excel_path, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=os.path.basename(excel_path),
        )

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)


def save_result_files(user_info, score, correct, total, time_taken, questions, answers):

    os.makedirs("results", exist_ok=True)
    filepath = os.path.join(
        "results",
        f"{user_info['name']}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx",
    )

    timed_out_count = answers.count(-1)

    summary_df = pd.DataFrame([{
        "Name": user_info["name"],
        "Phone": user_info["phone"],
        "University": user_info["uni"],
        "Exam Type": user_info["exam_type"],
        "Score %": score,
        "Correct": correct,
        "Incorrect": total - correct - timed_out_count,
        "Timed Out (Not Counted)": timed_out_count,
        "Total": total,
        "Time Taken": time_taken,
        "Exam Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }])

    details = []
    for i, q in enumerate(questions):
        ans = answers[i]
        correct_index = ord(q["answer"][0]) - 97

        if ans == -1:
            details.append({
                "Question": q["question"],
                "Candidate Answer": "No Answer",
                "Correct Answer": q["options"][correct_index],
                "Result": "Timed Out",
                "Mark": "⏱",
            })
        else:
            details.append({
                "Question": q["question"],
                "Candidate Answer": q["options"][ans],
                "Correct Answer": q["options"][correct_index],
                "Result": "Correct" if ans == correct_index else "Incorrect",
                "Mark": "✓" if ans == correct_index else "✗",
            })

    details_df = pd.DataFrame(details)

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        details_df.to_excel(writer, sheet_name="Details", index=False)

    try:
        send_result_email(filepath, user_info, score, timed_out_count)
    except Exception as e:
        print("Email error:", e)

    return filepath


def show_admin_panel():
    st.markdown("## Admin Panel")
    st.info("Admin panel loaded successfully.")
