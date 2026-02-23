import subprocess
import time
import webbrowser
import os
import sys

def start_taleweavers():
    print("==================================================")
    print("      T.A.L.E.W.E.A.V.E.R.S. LAUNCHER             ")
    print("==================================================")
    
    root_dir = os.path.dirname(os.path.abspath(__file__))
    vtt_dir = os.path.join(root_dir, "vtt")
    
    # 1. Start SAGA Brain (FastAPI)
    print("[1/3] Starting SAGA Brain Server...")
    # Executing from root_dir using brain.main:app to ensure package imports work
    brain_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "brain.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=root_dir,
        creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
    )
    
    # 2. Start VTT Frontend (Vite)
    print("[2/3] Starting Taleweaver VTT...")
    vtt_proc = subprocess.Popen(
        ["npm.cmd", "run", "dev"],
        cwd=vtt_dir,
        shell=True
    )
    
    # Wait for servers to warm up
    print("Warming up tactical relays...")
    time.sleep(5)
    
    # 3. Open Browser
    print("[3/3] Launching Strategic Interface...")
    webbrowser.open("http://127.0.0.1:5173")
    
    print("\n[READY] Tactical Link Established.")
    print("Press Ctrl+C to terminate the session.\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Terminating Taleweaver services...")
        brain_proc.terminate()
        vtt_proc.terminate()
        print("[DONE] Cleanup complete.")

if __name__ == "__main__":
    start_taleweavers()
