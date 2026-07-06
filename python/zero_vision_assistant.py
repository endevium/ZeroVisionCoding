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
        print(f"Opened Extension Development Host for {workspace_root}")
    except Exception as exc:
        print(f"Could not open Extension Development Host: {exc}")

def main() -> None:
    launch_extension_development_host()

    t0 = time.time()
    from zv.app import ZeroVisionAssistant
    print(f"Import zv.app took {time.time()-t0:.2f}s")

    t1 = time.time()
    app = ZeroVisionAssistant()
    print(f"Construct app took {time.time()-t1:.2f}s")

    from api.services import llm_service
    llm_service._ensure_qa_loaded()
    
    app.mainloop()

if __name__ == "__main__":
    main()