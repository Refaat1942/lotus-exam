import os
import json
import smtplib
from datetime import datetime
import pandas as pd
import streamlit as st
from email.message import EmailMessage

# ============================================================
# CONFIG
# ============================================================

RESULTS_FOLDER = "results"
RESULTS_CSV = "results.csv"
ADMIN_PASSWORD = "Lotus@@123"

# -------- EMAIL CONFIG --------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

SENDER_EMAIL = "ahmedrefat86@gmail.com"
SENDER_PASSWORD = "pcbpuynlxfaitxfn"  # ← حط App Password هنا
RECEIVER_EMAIL = "heba.darwish@lotuspharmacies.com"


# ============================================================
# SEND RESULT EMAIL
# ============================================================

def send_result_email(excel_path, user_info, score):
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

Please find the detailed Excel result attached.
"""
    )

    with open(excel_path, "rb") as f:
        file_data = f.read()
        file_name = os.path.basename(excel_path)

    msg.add_attachment(
        file_data,
        maintype="application",
        subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=file_name,
    )

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)


# ============================================================
# SAVE RESULT TO EXCEL
# ============================================================

def save_result_excel(user_info, score, correct, total, time_taken, questions, answers):

    exam_type = user_info.get("exam_type", "Exam")
    folder_path = os.path.join(RESULTS_FOLDER, exam_type.replace(" ", "_"))
    os.makedirs(folder_path, exist_ok=True)

    filename = f"{user_info.get('name').replace(' ', '_')}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"
    filepath = os.path.join(folder_path, filename)

    # -------- SUMMARY SHEET --------
    summary_data = [
        {
            "Name": user_info.get("name"),
            "Phone": user_info.get("phone"),
            "Graduation Year": user_info.get("year"),
            "University": user_info.get("uni"),
            "Exam Type": exam_type,
            "Exam Mode": "Online",
            "Score": f"{score:.0f}%",
            "Correct": correct,
            "Incorrect": total - correct,
            "Total": total,
            "Time Taken": time_taken,
            "Exam Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    ]

    summary_df = pd.DataFrame(summary_data)

    # -------- DETAILS SHEET --------
    details = []
    for i, q in enumerate(questions):

        chosen_index = answers[i]
        chosen_full = q["options"][chosen_index]

        correct_letter = q["answer"][0]
        correct_index = ord(correct_letter) - 97
        correct_full = q["options"][correct_index]

        is_correct = chosen_index == correct_index

        details.append(
            {
                "Question": q["question"],
                "Chosen Answer": chosen_full,
                "Correct Answer": correct_full,
                "Result": "Correct" if is_correct else "Incorrect",
                "Mark": "✔" if is_correct else "❌",
                "Category": q["category"],
                "Difficulty": q["difficulty"],
            }
        )

    details_df = pd.DataFrame(details)

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        details_df.to_excel(writer, sheet_name="Details", index=False)

    return filepath


# ============================================================
# SAVE RESULT FILES + EMAIL
# ============================================================

def save_result_files(user_info, score, correct, total, time_taken, questions, answers):

    filepath = save_result_excel(
        user_info=user_info,
        score=score,
        correct=correct,
        total=total,
        time_taken=time_taken,
        questions=questions,
        answers=answers,
    )

    # -------- SEND EMAIL --------
    try:
        send_result_email(filepath, user_info, score)
    except Exception as e:
        print("❌ Email sending failed:", e)

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
    try:
        return pd.read_csv(RESULTS_CSV)
    except:
        return pd.read_csv(RESULTS_CSV, on_bad_lines="skip")


# ============================================================
# ADMIN PANEL (كما هو)
# ============================================================

def show_admin_panel():
    st.markdown("## Admin Panel")

    if "admin_logged" not in st.session_state:
        st.session_state.admin_logged = False

    if not st.session_state.admin_logged:
        pw = st.text_input("Admin Password", type="password")
        if st.button("Login"):
            if pw == ADMIN_PASSWORD:
                st.session_state.admin_logged = True
                st.rerun()
            else:
                st.error("Wrong password.")
        return

    st.success("Logged in as Admin")

    all_rows = []

    for root, _, files in os.walk(RESULTS_FOLDER):
        for f in files:
            if f.endswith(".xlsx"):
                file_path = os.path.join(root, f)
                try:
                    df = pd.read_excel(file_path, sheet_name="Summary")
                    df["Excel Path"] = file_path
                    all_rows.append(df)
                except:
                    pass

    if not all_rows:
        st.warning("No results found")
        return

    df = pd.concat(all_rows, ignore_index=True)
    df["Exam Date"] = pd.to_datetime(df["Exam Date"], errors="coerce")
    df = df.sort_values("Exam Date", ascending=False)

    st.dataframe(df, use_container_width=True)
