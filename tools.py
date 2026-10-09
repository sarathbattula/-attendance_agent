import csv
import math
import re
from pathlib import Path

# Base paths relative to tools.py location
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CSV_PATH = DATA_DIR / "attendance.csv"
RULES_PATH = DATA_DIR / "rules.txt"

def get_attendance(student_id: str) -> dict:
    """
    Reads the attendance CSV file and returns the student's attendance records.

    Args:
        student_id: Unique string identifier for the student (e.g., 'S101').

    Returns:
        A dictionary containing student_id, name, classes_held, classes_attended, 
        and attendance_percentage (rounded to 2 decimal places).
        Returns an error dictionary if the student ID is not found.
    """
    cleaned_id = str(student_id).strip().upper()
    if not CSV_PATH.exists():
        return {"error": f"Attendance dataset not found at {CSV_PATH}"}
    
    try:
        with open(CSV_PATH, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["student_id"].strip().upper() == cleaned_id:
                    held = int(row["classes_held"])
                    attended = int(row["classes_attended"])
                    percent = round((attended / held * 100), 2) if held > 0 else 0.0
                    return {
                        "student_id": row["student_id"].strip(),
                        "name": row["name"].strip(),
                        "classes_held": held,
                        "classes_attended": attended,
                        "attendance_percentage": percent
                    }
        return {"error": f"Student ID '{student_id}' not found."}
    except Exception as e:
        return {"error": f"Failed to read attendance dataset: {str(e)}"}

def calculate_required_classes(attended: int, held: int, target_percent: float = 75.0) -> dict:
    """
    Calculates the minimum number of consecutive additional classes a student must attend
    (without missing any) to reach the target attendance percentage.

    Args:
        attended: Number of classes currently attended.
        held: Total number of classes held so far.
        target_percent: Target attendance percentage (default is 75.0). Must be strictly less than 100.

    Returns:
        A dictionary containing inputs, current percentage, required_classes, projected_attended, 
        projected_held, and projected_percentage.
    """
    try:
        target_percent = float(target_percent)
        attended = int(attended)
        held = int(held)
    except (ValueError, TypeError):
        return {"error": "Invalid numeric arguments provided to calculate_required_classes."}

    if target_percent >= 100.0 or target_percent <= 0.0:
        return {"error": "Target percentage must be strictly between 0 and 100."}
    if held <= 0:
        return {"error": "Total classes held must be greater than 0."}
    if attended < 0 or attended > held:
        return {"error": "Classes attended must be non-negative and cannot exceed total classes held."}

    current_percent = round((attended / held * 100), 2)
    if current_percent >= target_percent:
        return {
            "current_attended": attended,
            "current_held": held,
            "current_percentage": current_percent,
            "target_percent": target_percent,
            "required_classes": 0,
            "projected_attended": attended,
            "projected_held": held,
            "projected_percentage": current_percent,
            "message": f"Student is already at or above target attendance ({current_percent}% >= {target_percent}%)."
        }

    # Formula: x = ceil((target * held - 100 * attended) / (100 - target))
    numerator = (target_percent * held) - (100.0 * attended)
    denominator = 100.0 - target_percent
    required = math.ceil(numerator / denominator)
    required = max(0, required)

    new_attended = attended + required
    new_held = held + required
    new_percent = round((new_attended / new_held * 100), 2)

    return {
        "current_attended": attended,
        "current_held": held,
        "current_percentage": current_percent,
        "target_percent": target_percent,
        "required_classes": required,
        "projected_attended": new_attended,
        "projected_held": new_held,
        "projected_percentage": new_percent
    }

def search_rules(query: str) -> list[str]:
    """
    Performs a keyword search over the college attendance rules file and returns the top 3 matching rules.

    Args:
        query: Search prompt or query string regarding attendance policy.

    Returns:
        A list of up to 3 rule strings ranked by the number of keyword matches.
    """
    if not RULES_PATH.exists():
        return ["Error: Policy rules file not found."]

    try:
        with open(RULES_PATH, mode="r", encoding="utf-8") as f:
            rules = [line.strip() for line in f if line.strip()]

        stopwords = {
            "a", "an", "the", "is", "are", "was", "were", "for", "to", "in", "of", "and", "or", "on", 
            "can", "i", "my", "me", "how", "many", "do", "does", "need", "what", "if", "be", "get"
        }
        tokens = re.findall(r'\b\w+\b', str(query).lower())
        keywords = [t for t in tokens if len(t) > 1 and t not in stopwords]

        if not keywords:
            return rules[:3]

        scored_rules = []
        for rule in rules:
            rule_lower = rule.lower()
            # Count occurrences of keywords
            score = sum(rule_lower.count(kw) for kw in keywords)
            if score > 0:
                scored_rules.append((score, rule))

        scored_rules.sort(key=lambda x: x[0], reverse=True)
        results = [rule for _, rule in scored_rules[:3]]

        return results if results else rules[:3]
    except Exception as e:
        return [f"Error searching rules: {str(e)}"]
