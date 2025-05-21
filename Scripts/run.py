#!/usr/bin/env python3
"""
EthiViz - Cultural Bias Analysis Platform
Launcher script
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def main():
    """Run the EthiViz application"""
    print("Starting EthiViz - Cultural Bias Analysis Platform...")
    
    # Get the directory of this script
    script_dir = Path(__file__).parent.absolute()
    
    # Path to app.py
    app_path = script_dir / "app.py"
    
    if not app_path.exists():
        print(f"Error: Could not find app.py at {app_path}")
        sys.exit(1)
    
    # Check if venv exists and activate if it does
    venv_path = script_dir / "venv"
    if venv_path.exists():
        print("Using virtual environment...")
        python_path = venv_path / "bin" / "python"
        if not python_path.exists():
            # Try Windows path
            python_path = venv_path / "Scripts" / "python.exe"
            if not python_path.exists():
                print("Warning: Virtual environment exists but could not find python executable")
                python_path = "python"
    else:
        python_path = "python"
    
    # Install dependencies if needed
    try:
        # Check if requirements.txt exists
        req_path = script_dir / "requirements.txt"
        if req_path.exists():
            print("Installing dependencies...")
            subprocess.check_call([python_path, "-m", "pip", "install", "-r", str(req_path)], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        print("Warning: Failed to install required packages. Application may not function correctly.")
    
    # Launch Streamlit app
    print("Launching application...")
    try:
        # Start streamlit
        cmd = [python_path, "-m", "streamlit", "run", str(app_path), "--browser.serverAddress", "localhost", "--server.port", "8501"]
        process = subprocess.Popen(cmd)
        
        # Wait a bit for the server to start
        time.sleep(2)
        
        # Open web browser
        webbrowser.open("http://localhost:8501")
        
        print("\nEthiViz is running!")
        print("Application URL: http://localhost:8501")
        print("Press Ctrl+C to exit")
        
        # Keep the script running until user interrupts
        process.wait()
    
    except KeyboardInterrupt:
        print("\nShutting down EthiViz...")
        if 'process' in locals():
            process.terminate()
    except Exception as e:
        print(f"Error running application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()