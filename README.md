# Student Attendance Agent 🎓

A Python-based AI Agent built with the official **Google GenAI SDK (`google-genai`)** using **LLM Function Calling (Tool Calling)**. The agent dynamically fetches student records, performs exact mathematical computations, searches college attendance policies, and provides clear eligibility advice.

---

## 📁 Project Structure

```
attendance_agent/
├── data/
│   ├── attendance.csv     # Student attendance records (10 sample students)
│   └── rules.txt          # College attendance policy rules (9 rules)
├── tools.py               # Python functions registered as LLM tools
├── agent.py               # Agent loop, Gemini API function calling, & CLI
├── requirements.txt       # Project dependencies (google-genai, python-dotenv)
└── README.md              # Setup and usage documentation
```

---

## 🛠️ Tools Overview (`tools.py`)

1. `get_attendance(student_id: str) -> dict`  
   Reads `attendance.csv` and returns `student_id`, `name`, `classes_held`, `classes_attended`, and `attendance_percentage` (rounded to 2 decimal places).
2. `calculate_required_classes(attended: int, held: int, target_percent: float = 75.0) -> dict`  
   Calculates the minimum number of consecutive classes a student must attend (with 0 absences) to reach the target percentage using the formula:
   $$\text{required\_classes} = \left\lceil \frac{\text{target} \times \text{held} - 100 \times \text{attended}}{100 - \text{target}} \right\rceil$$
3. `search_rules(query: str) -> list[str]`  
   Performs a keyword-relevance search over `rules.txt` and returns the top 3 matching policy rules.

---

## 🚀 Setup & Execution Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Gemini API Key
Set your `GEMINI_API_KEY` in your environment or create a `.env` file in the `attendance_agent/` directory:

**Windows PowerShell:**
```powershell
$env:GEMINI_API_KEY="AIzaSyYourActualGeminiApiKey"
```

**Linux / macOS:**
```bash
export GEMINI_API_KEY="AIzaSyYourActualGeminiApiKey"
```

**Or using `.env` file:**
Create `attendance_agent/.env`:
```env
GEMINI_API_KEY=AIzaSyYourActualGeminiApiKey
```

### 3. Run the Agent CLI
```bash
python agent.py
```

*Note: If `GEMINI_API_KEY` is not provided, `agent.py` automatically runs in tool workflow simulation mode so you can test the multi-step tool execution without crashing.*

---

## ❓ 3 Example Queries

### Example 1: Student with High Attendance (>75%)
- **Student ID:** `S101` (Alice Vance - 85% Attendance)
- **User Question:** `"Can I attend exams? How many classes do I need?"`
- **Output:**
  ```text
  1. Current Attendance: 85/100 (85.0%)
  2. Classes Required: 0 consecutive classes required to reach 75% target.
  3. Relevant College Rule: 1. Direct Exam Eligibility: Students with a minimum overall attendance of 75% or higher are directly eligible to sit for semester examinations.
  4. Plain Language Explanation: Alice Vance currently has 85.0% attendance, which meets the college requirement of 75%. They are fully eligible to sit for exams without attending additional mandatory classes.
  ```

### Example 2: Student in Condonation Range (65% - 75%)
- **Student ID:** `S103` (Charlie Brown - 70% Attendance)
- **User Question:** `"What are the rules for condonation and medical leave?"`
- **Output:**
  ```text
  1. Current Attendance: 70/100 (70.0%)
  2. Classes Required: 20 consecutive classes required to reach 75% target.
  3. Relevant College Rule: 5. Medical Leave Counting: Approved medical leave (up to 10 days) permits condonation eligibility but does not directly count as attended classes in the percentage calculation.
  4. Plain Language Explanation: Charlie Brown has 70.0% attendance, putting them in the condonation category. They can become directly eligible by attending 20 more consecutive classes, or apply for condonation with a medical certificate and fee.
  ```

### Example 3: Student in Detention Range (<65%)
- **Student ID:** `S104` (Diana Prince - 60% Attendance)
- **User Question:** `"What happens if my attendance is below 65%?"`
- **Output:**
  ```text
  1. Current Attendance: 60/100 (60.0%)
  2. Classes Required: 60 consecutive classes required to reach 75% target.
  3. Relevant College Rule: 4. Detention Policy: Students with attendance below 65% are strictly detained from appearing in examinations and must re-register for the course in a subsequent semester.
  4. Plain Language Explanation: Diana Prince has 60.0% attendance, which is below the 65% threshold leading to detention. To reach 75%, they must attend 60 consecutive classes, or seek special Dean's approval.
  ```

---

## 🔄 Agent Execution Loop Scoping
- Native function calling tool schema registration with `google-genai` SDK.
- Loop iteration capped at **6 iterations**.
- All mathematical logic isolated strictly to Python functions (`tools.py`).
