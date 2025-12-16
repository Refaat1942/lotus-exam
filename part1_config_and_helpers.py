import re
from datetime import datetime
import os
import pandas as pd

# ---------------- CONFIG ----------------

ADMIN_PASSWORD = "Lotus@@123"
QUESTIONS_SHEET_URL = "https://docs.google.com/spreadsheets/d/1jqPa7h2gdBzBaZY1RZ4dSczKNFRbtpzX/export?format=xlsx"
RESULTS_CSV = "results.csv"
RESULTS_FOLDER = "results"  # Excel files per exam type


# ---------------- HELPERS ----------------

def clean_text(text):
    if text is None:
        return ""
    text = str(text)
    text = re.sub(r"[■□�••·•••]+", "", text)
    text = re.sub(r"\s+", " ", text)
    text = text.strip().lower()
    text = re.sub(r"^[^\w]+|[^\w]+$", "", text)
    return text


def load_questions_from_gsheet(url: str, sheet_name: str):
    df = pd.read_excel(url, sheet_name=sheet_name).fillna("")

    def safe_get(row, idx):
        try:
            val = row[idx]
            return "" if val is None else str(val).strip()
        except Exception:
            return ""

    qlist = []
    for i, row in df.iterrows():
        raw_q = safe_get(row, 0)
        if not raw_q:
            continue

        options = [safe_get(row, j) for j in range(1, 5) if safe_get(row, j)]
        correct_letter = safe_get(row, 6).lower()
        category = safe_get(row, 5) or "Other"
        difficulty = safe_get(row, 7) or "easy"

        qdict = {
            "question": f"Q{i+1}. {raw_q}",
            "qtext_clean": clean_text(raw_q),
            "options": [f"{chr(97 + j)}) {opt}" for j, opt in enumerate(options)],
            "answer": f"{correct_letter})" if correct_letter else "",
            "category": str(category).strip().lower(),
            "difficulty": str(difficulty).strip().lower(),
        }
        qlist.append(qdict)

    seen = set()
    deduped = []
    for q in qlist:
        key = q.get("qtext_clean", "")
        if key and key not in seen:
            seen.add(key)
            deduped.append(q)

    return deduped
