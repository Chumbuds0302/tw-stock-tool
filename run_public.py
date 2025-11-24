import os
import sys
import time
from pyngrok import ngrok
import subprocess

def run_public_app():
    # Set auth token explicitly
    ngrok.set_auth_token("2xrBkl3XgQq31ztyNa58KYFx5vV_7WzXwqqiGts3veWdtUiW6")

    # Kill any existing streamlit and ngrok processes
    subprocess.run(["taskkill", "/F", "/IM", "streamlit.exe"], capture_output=True)
    subprocess.run(["taskkill", "/F", "/IM", "ngrok.exe"], capture_output=True)

    # Start Streamlit in the background
    print("Starting Streamlit app...")
    streamlit_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8501", "--server.headless", "true"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Give it a moment to start
    time.sleep(3)

    # Open ngrok tunnel
    print("Opening ngrok tunnel...")
    try:
        public_url = ngrok.connect(8501).public_url
        print(f"Public URL: {public_url}")
        print("Keep this script running to maintain the public URL.")
    except Exception as e:
        print(f"Error opening ngrok tunnel: {e}")
        streamlit_process.kill()
        return

    try:
        # Keep the script running
        streamlit_process.wait()
    except KeyboardInterrupt:
        print("Stopping app...")
        ngrok.kill()
        streamlit_process.kill()

if __name__ == "__main__":
    run_public_app()
