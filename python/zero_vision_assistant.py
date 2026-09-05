import subprocess 
import time
from pathlib import Path

def launch_vs_code() -> None:
    workspace_root = Path(__file__).resolve().parents[1]

    try:
        subprocess.Popen(
            ["cmd", "/c", "code", "--new-window", "."],
            cwd=str(workspace_root), 
            stdout=subprocess.DEVNULL,  
            stderr=subprocess.DEVNULL,
        ) 
    except Exception as exc:
        print(f"Could not open VS Code: {exc}")

def main() -> None:
    launch_vs_code()
    from zv.app import ZeroVisionAssistant
    app = ZeroVisionAssistant()

    from api.services import llm_service
    llm_service._ensure_qa_loaded()
    
    app.mainloop()

if __name__ == "__main__":
    main()