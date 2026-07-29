import os
import sys
import json
import time
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

# Load .env file
PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

# Ensure the python directory is in sys.path so we can import the backend
sys.path.insert(0, str(PROJECT_ROOT / "python"))

from api.services.llm_service import llm_fix_python_error, llm_code_review, llm_analyze, llm_explain_symbol

# Configure Groq
api_key = os.environ.get("GROQ_API_KEY", "")
if not api_key:
    print("ERROR: GROQ_API_KEY not found in .env file or environment.")
    sys.exit(1)

client = Groq(api_key=api_key)
JUDGE_MODEL = "llama-3.3-70b-versatile"

def ask_groq_judge(system_instruction, user_prompt, max_retries=3):
    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=JUDGE_MODEL,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )
            text = response.choices[0].message.content or "{}"
            return json.loads(text)
        except Exception as e:
            error_str = str(e)
            if "429" in error_str and attempt < max_retries:
                wait = (attempt + 1) * 15  # 15s, 30s, 45s
                print(f"  Rate limited. Retrying in {wait}s (attempt {attempt+1}/{max_retries})...")
                time.sleep(wait)
                continue
            print(f"Groq API error: {e}")
            return {}

def test_fixer(test_cases_dir):
    print("Testing Code Fixer...")
    results = []
    fixer_dir = test_cases_dir / "fixer"
    if not fixer_dir.exists(): return []

    for test_file in fixer_dir.glob("*.json"):
        with open(test_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        code = data.get("code", "")
        error_msg = data.get("error", "")
        
        print(f"  -> Running {test_file.name}...")
        start_time = time.time()
        
        fix_response = llm_fix_python_error(code=code, error=error_msg)
        content = fix_response.get("content", "")
        duration = time.time() - start_time
        
        # Deterministic check: Runtime Success Rate
        runtime_success = 0.0
        fix_success = 0.0
        
        if content.strip():
            fix_success = 1.0
            temp_file = test_cases_dir / "_temp_fixer_exec.py"
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(content)
                
            try:
                proc = subprocess.run([sys.executable, str(temp_file)], capture_output=True, text=True, timeout=5)
                if proc.returncode == 0:
                    runtime_success = 1.0
            except Exception:
                pass
            finally:
                if temp_file.exists(): os.remove(temp_file)
                
        # Subjective check via Groq
        prompt = f"""
        Original Code:
        {code}
        
        Traceback:
        {error_msg}
        
        1.5B Model's Patched Code:
        {content}
        
        Evaluate the following metrics (0.0 to 1.0):
        "Error Detection Accuracy": Did the patch address the actual root cause of the error?
        "Logic Preservation Rate": Did the patch maintain the original behavior without deleting unrelated functions?
        
        Return ONLY JSON: {{"Error Detection Accuracy": float, "Logic Preservation Rate": float}}
        """
        judge_res = ask_groq_judge("You are a strict code evaluator.", prompt)
        
        results.append({
            "name": test_file.name,
            "Error Detection Accuracy": judge_res.get("Error Detection Accuracy", 0.0),
            "Fix Success Rate": fix_success,
            "Runtime Success Rate": runtime_success,
            "Logic Preservation Rate": judge_res.get("Logic Preservation Rate", 0.0),
            "Response Time": duration
        })
        
    return results

def test_reviewer(test_cases_dir):
    print("Testing Code Reviewer...")
    results = []
    reviewer_dir = test_cases_dir / "reviewer"
    if not reviewer_dir.exists(): return []

    for test_file in reviewer_dir.glob("*.json"):
        with open(test_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        code = data.get("code", "")
        expected_bugs = data.get("expected_bugs", [])
        
        print(f"  -> Running {test_file.name}...")
        start_time = time.time()
        
        review_response = llm_code_review(code=code, language="python")
        duration = time.time() - start_time
        
        issues = review_response.get("issues", [])
        
        prompt = f"""
        Original Code:
        {code}
        
        Expected Real Bugs: {expected_bugs}
        
        1.5B Model's Reported Issues:
        {json.dumps(issues, indent=2)}
        
        Evaluate the following metrics (0.0 to 1.0):
        "Issue Detection Accuracy": Did it find the expected bugs? (Recall-like)
        "False Positive Rate": Did it hallucinate bugs that don't exist? (0.0 is perfect, 1.0 means everything was fake)
        "Suggestion Quality": Are the proposed fixes in the issues logical?
        "Severity Classification Accuracy": Are the 'critical' vs 'low' labels correct?
        
        Return ONLY JSON: {{"Issue Detection Accuracy": float, "False Positive Rate": float, "Suggestion Quality": float, "Severity Classification Accuracy": float}}
        """
        judge_res = ask_groq_judge("You are a strict code evaluator.", prompt)
        
        res_dict = {
            "name": test_file.name,
            "Response Time": duration
        }
        res_dict.update(judge_res)
        # Handle failures in API
        for k in ["Issue Detection Accuracy", "False Positive Rate", "Suggestion Quality", "Severity Classification Accuracy"]:
            if k not in res_dict: res_dict[k] = 0.0
            
        results.append(res_dict)
        
    return results

def test_analyze(test_cases_dir):
    print("Testing Analyze Code...")
    results = []
    analyze_dir = test_cases_dir / "analyze"
    if not analyze_dir.exists(): return []

    for test_file in analyze_dir.glob("*.json"):
        with open(test_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        code = data.get("code", "")
        
        print(f"  -> Running {test_file.name}...")
        start_time = time.time()
        analyze_response = llm_analyze(code=code, language="python")
        duration = time.time() - start_time
        
        prompt = f"""
        Original Code:
        {code}
        
        1.5B Model's Analysis:
        {json.dumps(analyze_response, indent=2)}
        
        Evaluate the following metrics (0.0 to 1.0):
        "Analysis Accuracy": Does the summary reflect the code's overarching purpose?
        "Logic Explanation Accuracy": Are the step-by-step logic breakdowns correct?
        "Issue Detection Rate": Did it spot any obvious smells (if any exist)?
        "Suggestion Relevance": Are the proposed improvements practical?
        
        Return ONLY JSON: {{"Analysis Accuracy": float, "Logic Explanation Accuracy": float, "Issue Detection Rate": float, "Suggestion Relevance": float}}
        """
        judge_res = ask_groq_judge("You are a strict code evaluator.", prompt)
        
        res_dict = {"name": test_file.name, "Response Time": duration}
        res_dict.update(judge_res)
        for k in ["Analysis Accuracy", "Logic Explanation Accuracy", "Issue Detection Rate", "Suggestion Relevance"]:
            if k not in res_dict: res_dict[k] = 0.0
        results.append(res_dict)
        
    return results

def test_explain(test_cases_dir):
    print("Testing Explain Code...")
    results = []
    explain_dir = test_cases_dir / "explain"
    if not explain_dir.exists(): return []

    for test_file in explain_dir.glob("*.json"):
        with open(test_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        code = data.get("code", "")
        symbol = data.get("target", "")
        kind = data.get("kind", "")
        
        print(f"  -> Running {test_file.name}...")
        start_time = time.time()
        explain_response = llm_explain_symbol(code=code, symbol=symbol, language="python", kind=kind)
        duration = time.time() - start_time
        
        prompt = f"""
        Original Code:
        {code}
        Target Symbol to Explain: {symbol}
        
        1.5B Model's Explanation:
        {json.dumps(explain_response, indent=2)}
        
        Evaluate the following metrics (0.0 to 1.0):
        "Explanation Accuracy": Is the explanation of the specific symbol correct?
        "Context Awareness": Does it correctly reference how it interacts with the rest of the file?
        "Terminology Correctness": Is technical jargon used correctly?
        "Completeness": Did it explain all critical parts?
        
        Return ONLY JSON: {{"Explanation Accuracy": float, "Context Awareness": float, "Terminology Correctness": float, "Completeness": float}}
        """
        judge_res = ask_groq_judge("You are a strict code evaluator.", prompt)
        
        res_dict = {"name": test_file.name, "Response Time": duration}
        res_dict.update(judge_res)
        for k in ["Explanation Accuracy", "Context Awareness", "Terminology Correctness", "Completeness"]:
            if k not in res_dict: res_dict[k] = 0.0
        results.append(res_dict)
        
    return results

def main():
    test_cases_dir = PROJECT_ROOT / "tests" / "ai_test_cases"
    
    fixer_results = test_fixer(test_cases_dir)
    reviewer_results = test_reviewer(test_cases_dir)
    analyze_results = test_analyze(test_cases_dir)
    explain_results = test_explain(test_cases_dir)
    
    report = "# AI Accuracy Report (LLM-as-a-Judge)\n\n"
    report += "Evaluated using Groq for subjective metrics.\n\n"
    
    def format_results(title, results):
        if not results:
            return f"## {title}\nNo tests found.\n\n"
        
        out = f"## {title}\n"
        keys = [k for k in results[0].keys() if k not in ("name", "Response Time")]
        
        for k in keys:
            avg = sum(r.get(k, 0.0) for r in results) / len(results)
            # if it's a rate where lower is better (like False Positive Rate), we still just print the average
            out += f"- **{k}:** {avg*100:.1f}%\n"
            
        avg_time = sum(r.get("Response Time", 0.0) for r in results) / len(results)
        out += f"- **Average Response Time:** {avg_time:.2f}s\n\n"
        
        out += "### Log\n"
        for r in results:
            out += f"- `{r['name']}`: "
            metrics = [f"{k}={r.get(k,0.0):.2f}" for k in keys]
            out += ", ".join(metrics)
            out += f" ({r.get('Response Time',0):.1f}s)\n"
        out += "\n"
        return out
        
    report += format_results("Code Debugging (Fixer)", fixer_results)
    report += format_results("Code Review", reviewer_results)
    report += format_results("Analyze Code", analyze_results)
    report += format_results("Explain Code", explain_results)
    
    report_path = PROJECT_ROOT / "accuracy_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"\nReport generated at {report_path}")

if __name__ == "__main__":
    main()
