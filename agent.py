import os
import sys

# Ensure UTF-8 output encoding for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Load environment variables from .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import tools

SYSTEM_PROMPT = (
    "You are a student attendance assistant. Always use get_attendance for the student's data, "
    "calculate_required_classes for any computation, and search_rules for policy questions. "
    "Never guess numbers or rules. Reply concisely.\n\n"
    "Your final answer MUST strictly include the following 4 sections:\n"
    "1. Current Attendance: [attended/held and percentage]\n"
    "2. Classes Required: [number of consecutive classes required to reach target percentage, default 75%]\n"
    "3. Relevant College Rule: [quote or summarize the applicable college attendance policy]\n"
    "4. Plain Language Explanation: [2-3 sentence explanation regarding exam eligibility, condonation, or detention]"
)

TOOL_MAP = {
    "get_attendance": tools.get_attendance,
    "calculate_required_classes": tools.calculate_required_classes,
    "search_rules": tools.search_rules,
}

def run_agent_llm(student_id: str, question: str, api_key: str, model_name: str = "gemini-3.6-flash") -> str:
    """
    Executes the multi-step agent loop using the official Google GenAI SDK (google-genai).
    Registers tools, processes tool calls from Gemini, and returns the final answer.
    Capped at 6 iterations.
    """
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=[tools.get_attendance, tools.calculate_required_classes, tools.search_rules],
        temperature=0.0,
    )

    user_prompt = f"Student ID: {student_id}. Question: {question}"
    print(f"\n" + "=" * 65)
    print(f"[AGENT INITIATED] (Gemini LLM)")
    print(f"   Student ID : {student_id}")
    print(f"   Question   : {question}")
    print("=" * 65)

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_prompt)]
        )
    ]

    max_iterations = 6

    for iteration in range(1, max_iterations + 1):
        print(f"\n--- [Iteration {iteration}/{max_iterations}] Querying Gemini model ({model_name}) ---")
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
        except Exception as e:
            return f"API Error: {str(e)}"

        # Check if model requested tool calls
        if response.function_calls:
            # Append model's output (with function call requests) to contents history
            if response.candidates and response.candidates[0].content:
                contents.append(response.candidates[0].content)

            tool_response_parts = []
            for call in response.function_calls:
                fn_name = call.name
                fn_args = call.args or {}

                print(f"  [Tool Call] {fn_name}({fn_args})")

                if fn_name in TOOL_MAP:
                    try:
                        tool_result = TOOL_MAP[fn_name](**fn_args)
                    except Exception as err:
                        tool_result = {"error": f"Execution error in {fn_name}: {str(err)}"}
                else:
                    tool_result = {"error": f"Unknown tool '{fn_name}'"}

                print(f"  [Tool Result] {tool_result}")

                # Format tool output dict for FunctionResponsePart
                resp_payload = tool_result if isinstance(tool_result, dict) else {"result": tool_result}
                tool_part = types.Part.from_function_response(
                    name=fn_name,
                    response=resp_payload
                )
                tool_response_parts.append(tool_part)

            # Append tool execution results back into history with 'user' role
            contents.append(types.Content(role="user", parts=tool_response_parts))
        else:
            # Model returned final text answer
            print("  [Done] Final Answer Received.")
            return response.text.strip() if response.text else "No content returned."

    return "Agent loop reached maximum iteration limit (6) without finishing."


def run_agent_demo(student_id: str, question: str) -> str:
    """
    Simulates the exact agent workflow and tool calling loop deterministically
    when no GEMINI_API_KEY is configured. Uses tools.py for all arithmetic and lookup.
    """
    print(f"\n" + "=" * 65)
    print(f"[AGENT INITIATED] (Workflow Simulation)")
    print(f"   Student ID : {student_id}")
    print(f"   Question   : {question}")
    print("=" * 65)

    print("\n--- [Iteration 1/6] Executing Tool: get_attendance ---")
    fn_name = "get_attendance"
    fn_args = {"student_id": student_id}
    print(f"  [Tool Call] {fn_name}({fn_args})")
    att_res = tools.get_attendance(student_id)
    print(f"  [Tool Result] {att_res}")

    if "error" in att_res:
        return f"Error: {att_res['error']}"

    print("\n--- [Iteration 2/6] Executing Tool: calculate_required_classes ---")
    fn_name = "calculate_required_classes"
    fn_args = {
        "attended": att_res["classes_attended"],
        "held": att_res["classes_held"],
        "target_percent": 75.0
    }
    print(f"  [Tool Call] {fn_name}({fn_args})")
    calc_res = tools.calculate_required_classes(**fn_args)
    print(f"  [Tool Result] {calc_res}")

    print("\n--- [Iteration 3/6] Executing Tool: search_rules ---")
    fn_name = "search_rules"
    fn_args = {"query": question}
    print(f"  [Tool Call] {fn_name}({fn_args})")
    rules_res = tools.search_rules(question)
    print(f"  [Tool Result] {rules_res}")

    pct = att_res["attendance_percentage"]
    req = calc_res.get("required_classes", 0)
    name = att_res["name"]
    held = att_res["classes_held"]
    attended = att_res["classes_attended"]
    top_rule = rules_res[0] if rules_res else "No specific rule found."

    if pct >= 75.0:
        status_desc = f"{name} currently has {pct}% attendance, which meets the college requirement of 75%. They are fully eligible to sit for exams without attending additional mandatory classes."
    elif pct >= 65.0:
        status_desc = f"{name} has {pct}% attendance, putting them in the condonation category. They can become directly eligible by attending {req} more consecutive classes, or apply for condonation with a medical certificate and fee."
    else:
        status_desc = f"{name} has {pct}% attendance, which is below the 65% threshold leading to detention. To reach 75%, they must attend {req} consecutive classes, or seek special Dean's approval."

    final_answer = (
        f"1. Current Attendance: {attended}/{held} ({pct}%)\n"
        f"2. Classes Required: {req} consecutive classes required to reach 75% target.\n"
        f"3. Relevant College Rule: {top_rule}\n"
        f"4. Plain Language Explanation: {status_desc}"
    )
    print("  [Done] Final Answer Received.")
    return final_answer


def run_agent(student_id: str, question: str) -> str:
    """
    Main entry point for running the Student Attendance Agent.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    model_name = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")

    if api_key and api_key.strip() and api_key != "YOUR_GEMINI_API_KEY_HERE":
        res = run_agent_llm(student_id, question, api_key=api_key, model_name=model_name)
        if res.startswith("API Error:") and ("RESOURCE_EXHAUSTED" in res or "429" in res):
            print("\n[Notice] Gemini API rate limit encountered. Falling back to deterministic tool simulation mode...\n")
            return run_agent_demo(student_id, question)
        return res
    else:
        print("\n[Notice] GEMINI_API_KEY environment variable not set.")
        print("[Notice] Running agent in tool-execution workflow simulation mode.\n")
        return run_agent_demo(student_id, question)


def main():
    """
    Interactive CLI for the Student Attendance Agent.
    """
    print("\n" + "*" * 65)
    print("      STUDENT ATTENDANCE AGENT (Gemini Function Calling)")
    print("*" * 65)
    print("Type 'exit' or 'quit' at any prompt to stop.\n")

    default_question = "Can I attend exams? How many classes do I need?"

    while True:
        try:
            student_id = input("\nEnter Student ID (e.g., S101, S103, S104) [default: S103]: ").strip()
            if student_id.lower() in ("exit", "quit"):
                print("Goodbye!")
                break
            if not student_id:
                student_id = "S103"

            question = input(f"Enter Question [default: '{default_question}']: ").strip()
            if question.lower() in ("exit", "quit"):
                print("Goodbye!")
                break
            if not question:
                question = default_question

            answer = run_agent(student_id, question)
            print("\n" + "─" * 65)
            print("FINAL ANSWER:")
            print(answer)
            print("─" * 65)

        except KeyboardInterrupt:
            print("\nExiting agent CLI. Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")


if __name__ == "__main__":
    main()
