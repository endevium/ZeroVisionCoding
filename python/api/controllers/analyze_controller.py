from api.services.code_analyzer import analyze_code_logic

def analyze_code_controller(code: str, language: str):
    issues = analyze_code_logic(code, language)

    return {
        "language": language,
        "issues": issues,
        "message": "Analysis complete"
    }
