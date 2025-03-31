import subprocess
import sys
import os

def start_uvicorn_detached():
    # Change these parameters as needed for your specific API
    host = "0.0.0.0"
    port = "8080"
    app_module = "api:app"  # Replace with your actual module:app
    
    # Construct the command
    command = f"nohup uvicorn {app_module} --host {host} --port {port} --reload > uvicorn.log 2>&1 &"
    
    print(f"Starting uvicorn server with command: {command}")
    subprocess.run(command, shell=True)
    print(f"Server started! Check uvicorn.log for output.")
    print(f"To stop the server, find its PID with 'ps aux | grep uvicorn' and use 'kill <PID>'")

if __name__ == "__main__":
    start_uvicorn_detached()