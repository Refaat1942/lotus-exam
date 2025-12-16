import re
import random
from typing import List, Dict
from part1_config_and_helpers import clean_text

# ===========================================================
# VALIDATION (نفس القديم – بدون أي تغيير)
# ===========================================================

def validate_candidate_inputs(name: str, phone: str, year: str, uni: str, exam_type: str):
    if not re.match(r"^[A-Za-z ]+$", name.strip()):
        return False, "Name must contain only letters."
    if not re.match(r"^(010|011|012|015)\d{8}$", phone.strip()):
        return False, "Phone must be 11 digits and start with 010/011/012/015."
    if not re.match(r"^\d{4}$", year.strip()):
        return False, "Graduation Year must be 4 digits."
    if not re.match(r"^[A-Za-z0-9 ]+$", uni.strip()):
        return False, "University must contain only letters and numbers."
    if not exam_type:
        return False, "Please choose an Exam Type."
    return True, ""

# ===========================================================
# NEW EXAM RULES (حسب الجدول اللي إنت بعته)
# ===========================================================

EXAM_RULES = {
    "Pharmacist (New Hire)": {
        "total": 20,
        "categories": {"drug": 10, "cosmetics": 10},
        "difficulty": {"easy": 2, "medium": 15, "difficult": 3},
    },
    "Assistant (New Hire)": {
        "total": 20,
        "categories": {"assistant": 20},
        "difficulty": {"easy": 6, "medium": 10, "difficult": 4},
    },
    "Proficiency Bonus - Pharmacist": {
        "total": 30,
        "categories": {"drug": 10, "cosmetics": 10, "management": 5, "operations": 5},
        "difficulty": {"easy": 5, "medium": 15, "difficult": 10},
    },
    "Proficiency Bonus - Assistant": {
        "total": 30,
        "categories": {"assistant": 30},
        "difficulty": {"easy": 5, "medium": 15, "difficult": 10},
    },
    "Branch Manager Promotion": {
        "total": 30,
        "categories": {"drug": 10, "cosmetics": 10, "management": 10, "operations": 10},
        "difficulty": {"easy": 5, "medium": 10, "difficult": 15},
    },
    "Shift Manager Promotion": {
        "total": 30,
        "categories": {"drug": 10, "cosmetics": 10, "management": 10, "operations": 10},
        "difficulty": {"easy": 5, "medium": 15, "difficult": 10},
    },
}

# ===========================================================
# NORMALIZE DIFFICULTY
# ===========================================================

def normalize_diff(d: str) -> str:
    d = (d or "").strip().lower()
    if d in ("easy", "e"): return "easy"
    if d in ("medium", "med", "m"): return "medium"
    if d in ("difficult", "hard", "diff", "d", "h"): return "difficult"
    return "medium"

# ===========================================================
# BUILD CATEGORY POOL
# ===========================================================

def build_category_pool(bank: List[Dict], cat_name: str):
    items = {}
    for q in bank:
        cat = str(q.get("category", "")).strip().lower()
        if cat != cat_name:
            continue
        key = q.get("qtext_clean") or clean_text(q.get("question", ""))
        if not key or key in items:
            continue
        q_copy = q.copy()
        q_copy["difficulty"] = normalize_diff(q_copy.get("difficulty", ""))
        items[key] = q_copy
    return list(items.values())

# ===========================================================
# PICK QUESTIONS WITH DIFFICULTY DISTRIBUTION
# ===========================================================

def pick_from_pool(pool, target_count, diff_rules):
    by_diff = {"easy": [], "medium": [], "difficult": []}

    for q in pool:
        d = q["difficulty"]
        if d not in by_diff:
            d = "medium"
        by_diff[d].append(q)

    for lst in by_diff.values():
        random.shuffle(lst)

    selected = []
    used = set()
    remaining = target_count

    # 1) pick required difficulty counts
    for diff_name, need in diff_rules.items():
        lst = by_diff.get(diff_name, [])
        while need > 0 and lst:
            q = lst.pop()
            key = q["qtext_clean"]
            if key in used:
                continue
            used.add(key)
            selected.append(q)
            remaining -= 1
            need -= 1

    # 2) fill remaining
    leftovers = []
    for lst in by_diff.values():
        leftovers.extend(lst)
    random.shuffle(leftovers)

    for q in leftovers:
        if remaining <= 0:
            break
        key = q["qtext_clean"]
        if key in used:
            continue
        used.add(key)
        selected.append(q)
        remaining -= 1

    return selected

# ===========================================================
# MAIN: SELECT QUESTIONS FOR EXAM
# ===========================================================

def select_questions_for_exam(exam_type: str, bank: List[Dict]):

    if exam_type not in EXAM_RULES:
        return [], f"No rules defined for exam type: {exam_type}"

    rules = EXAM_RULES[exam_type]
    total_required = rules["total"]
    categories_rules = rules["categories"]
    difficulty_rules = rules["difficulty"]

    final_questions = []

    # -------------------------------------------------------
    # PICK QUESTIONS PER CATEGORY
    # -------------------------------------------------------
    for cat_name, count in categories_rules.items():

        pool = build_category_pool(bank, cat_name)
        if len(pool) < count:
            return [], f"Not enough questions in category '{cat_name}'"

        # scale difficulty portion for this category
        diff_scaled = {}
        for d_name, d_total in difficulty_rules.items():
            diff_scaled[d_name] = round(d_total * (count / total_required))

        selected = pick_from_pool(pool, count, diff_scaled)
        if len(selected) < count:
            return [], f"Not enough questions for category '{cat_name}' with required difficulty"

        final_questions.extend(selected)

    random.shuffle(final_questions)

    return final_questions[:total_required], ""
