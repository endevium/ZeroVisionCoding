import subprocess
import time
from pathlib import Path

def launch_extension_development_host() -> None:
    workspace_root = Path(__file__).resolve().parents[1]

    try:
        subprocess.Popen(
            ["cmd", "/c", "code", "--new-window", f"--extensionDevelopmentPath={workspace_root}"],
            cwd=str(workspace_root),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(f"Opened VS Code for {workspace_root}")
    except Exception as exc:
        print(f"Could not open VS Code: {exc}")

def main() -> None:
    #launch_extension_development_host()
    from zv.app import ZeroVisionAssistant
    app = ZeroVisionAssistant()

    from api.services import llm_service
    llm_service._ensure_qa_loaded()
    
    app.mainloop()

if __name__ == "__main__":
    main()