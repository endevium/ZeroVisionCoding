def analyze_code_logic(code: str, language: str):
    issues = []

    if "print(" in code:
        issues.append("Uses print statement")

    return issues