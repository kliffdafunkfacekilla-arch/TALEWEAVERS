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
    brain_dir = os.path.join(root_dir, "brain")
    vtt_dir = os.path.join(root_dir, "vtt")
    
    # 1. Start SAGA Brain (FastAPI)
    print("[1/3] Starting SAGA Brain Server...")
    brain_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "server:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=brain_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # 2. Start VTT Frontend (Vite)
    print("[2/3] Starting Taleweaver VTT...")
    vtt_proc = subprocess.Popen(
        ["npm.cmd", "run", "dev"],
        cwd=vtt_dir,
        shell=True
    )
    
    # Wait for servers to warm up
    time.sleep(3)
    
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
