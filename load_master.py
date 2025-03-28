import subprocess
import os
from datetime import datetime
import time

# Global variables
locust_process = None

def run_locust_master(host, headless, users, spawn_rate, ramp_time, script_path, workers):
    """
    Runs Locust in Master mode.
    """
    global locust_process

    command = [
        "locust",
        "-f", script_path,
        "--master",
        "--web-port", "8088",
        "--expect-workers", str(workers),
    ]

    # Headless mode settings
    if headless:
        command.extend(["--headless", "-u", str(users), "-r", str(spawn_rate), "-t", ramp_time])

    locust_process = subprocess.Popen(command)

def stop_locust():
    """Stops the Locust Master/Worker process and disconnects the Locust web interface."""
    global locust_process

    # Stop the Locust master process (if running)
    if locust_process:
        locust_process.terminate()
        locust_process.wait()  # Ensure the process is fully terminated
        locust_process = None

def save_uploaded_file(uploaded_file, upload_dir="uploads"):
    """
    Saves the uploaded file with a unique name in the specified directory.
    """
    # Create the upload directory if it doesn't exist
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    # Generate a unique filename using a timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{uploaded_file.name}"
    file_path = os.path.join(upload_dir, filename)

    # Save the file
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return file_path

def get_latest_script(upload_dir="uploads"):
    """
    Returns the path of the latest uploaded script file.
    """
    if not os.path.exists(upload_dir):
        return None

    # Get all files in the upload directory
    files = [f for f in os.listdir(upload_dir) if f.endswith(".py")]
    if not files:
        return None

    # Find the latest file based on modification time
    latest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(upload_dir, f)))
    return os.path.join(upload_dir, latest_file)

def get_system_ip():
    """
    Fetches the system's IP address.
    """
    try:
        # Create a socket connection to a remote server (e.g., Google DNS)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))  # Connect to Google's public DNS server
            ip_address = s.getsockname()[0]  # Get the local IP address
        return ip_address
    except Exception as e:
        return "localhost"  # Fallback to localhost if IP cannot be fetched