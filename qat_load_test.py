import streamlit as st
import os
import subprocess
import socket
import json
import threading
import requests

STATUS_FILE = "master_status.json"
WORKER_IPS_FILE = "worker_ips.json"


def save_master_status(is_running, master_ip, selected_file):
    """Saves the master status in a file to share across users."""
    status_data = {
        "is_master_running": is_running,
        "master_ip": master_ip,
        "selected_master_file": selected_file
    }
    with open(STATUS_FILE, "w") as f:
        json.dump(status_data, f)


def load_master_status():
    """Loads the master status from the file."""
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f:
            return json.load(f)
    return {"is_master_running": False, "master_ip": None, "selected_master_file": None}


def save_worker_ips(worker_ips):
    """Saves the worker IPs in a file."""
    with open(WORKER_IPS_FILE, "w") as f:
        json.dump(worker_ips, f)


def load_worker_ips():
    """Loads the worker IPs from the file."""
    if os.path.exists(WORKER_IPS_FILE):
        with open(WORKER_IPS_FILE, "r") as f:
            return json.load(f)
    return []


def get_system_ip():
    """Gets the system IP address."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception as e:
        st.error(f"Failed to fetch system IP: {e}")
        return "localhost"


def get_locust_files():
    """Lists available .py files in the uploads folder."""
    UPLOADS_FOLDER = "uploads"
    return [f for f in os.listdir(UPLOADS_FOLDER) if f.endswith(".py")]


def create_bat_file(mode, master_ip, locust_file, host):
    """Creates and executes .bat files for Master or Worker with absolute paths."""
    bat_filename = f"{mode.lower()}.bat"
    locust_file_path = os.path.abspath(os.path.join("uploads", locust_file))
    bat_path = os.path.abspath(bat_filename)

    bat_content = (
        f"@echo off\n"
        f"echo Starting Locust in {mode} Mode...\n"
        f"locust -f \"{locust_file_path}\" --host={host} "
    )

    if mode == "Master":
        bat_content += "--web-port 8088 --master\n"
    else:
        bat_content += f"--worker --master-host={master_ip}\n"

    bat_content += "pause"

    with open(bat_path, "w") as f:
        f.write(bat_content)

    return bat_path


def is_worker_alive(worker_ip):
    """Check if a worker is still responsive by sending a small request."""
    try:
        response = requests.get(f"http://{worker_ip}:8089", timeout=2)
        return response.status_code == 200
    except requests.RequestException:
        return False


def clean_disconnected_workers():
    """Remove workers that are no longer responding."""
    worker_ips = load_worker_ips()
    active_workers = [ip for ip in worker_ips if is_worker_alive(ip)]
    save_worker_ips(active_workers)


def start_worker(master_ip, selected_file):
    """Starts the Worker and ensures a terminal is opened correctly."""
    bat_file_path = create_bat_file("Worker", master_ip, selected_file, "http://localhost")
    worker_ip = get_system_ip()

    worker_ips = load_worker_ips()
    if worker_ip not in worker_ips:
        worker_ips.append(worker_ip)
        save_worker_ips(worker_ips)

    # Open terminal correctly on different OS
    try:
        if os.name == "nt":  # Windows
            subprocess.Popen(["cmd.exe", "/c", "start", "cmd", "/k", bat_file_path], shell=True)
        else:  # macOS/Linux
            subprocess.Popen(["x-terminal-emulator", "-e", f"bash -c '{bat_file_path}; exec bash'"])
        st.success(f"Worker started successfully! IP: {worker_ip}")
    except Exception as e:
        st.error(f"Failed to start worker terminal: {e}")


class loadTest():

    def load_test_page():
        logged_in_user = st.session_state.username
        is_superadmin = logged_in_user == "superadmin"

        if is_superadmin:
            mode = "Master"
            st.session_state["is_master_running"] = False  # Track Master status
        else:
            mode = "Worker"

        st.write(f"### {mode} Load Configuration - {logged_in_user}")

        UPLOADS_FOLDER = "uploads"
        os.makedirs(UPLOADS_FOLDER, exist_ok=True)

        # Master Mode (Only for Superadmin)
        if is_superadmin:
            locust_files = get_locust_files()
            master_ip = get_system_ip()
            status = load_master_status()

            st.write(f"Detected Master IP: `{master_ip}`")

            if locust_files:
                selected_file = st.selectbox("Select Locust Test File", locust_files)
                st.markdown("**Files are attached. Click on start!**")
            else:
                selected_file = None
                st.warning("No Locust test scripts found in `uploads` folder!")

            if st.button("Start Master"):
                if not selected_file:
                    st.error("No test script selected!")
                else:
                    save_master_status(True, master_ip, selected_file)
                    bat_file_path = create_bat_file("Master", master_ip, selected_file, "http://localhost")
                    subprocess.Popen(bat_file_path, shell=True)
                    st.success(f"Master started successfully with `{selected_file}`. Workers can now connect")

            if st.button("Stop Master"):
                subprocess.call("taskkill /F /IM locust.exe", shell=True)
                save_master_status(False, None, None)
                save_worker_ips([])  # Clear Worker IPs
                st.success("Master stopped!")
                st.markdown("**All Workers should disconnect!**")

            # Display Worker IPs
            clean_disconnected_workers()  # Clean inactive workers before displaying
            worker_ips = load_worker_ips()
            if worker_ips:
                st.write("### Connected Workers")
                for ip in worker_ips:
                    st.write(f"- {ip}")
            else:
                st.write("No Workers connected yet.")

        # Worker Mode (For all non-superadmin users)
        else:
            status = load_master_status()

            if not status["is_master_running"]:
                st.warning("Worker mode is disabled until Master starts!")
                st.stop()

            selected_file = status["selected_master_file"]
            master_ip = status["master_ip"]

            st.write(f"Using Locust Test File: `{selected_file}`")
            st.write(f"Connecting to Master at `{master_ip}`")

            if st.button("Start Worker"):
                start_worker(master_ip, selected_file)

            if st.button("Stop Worker"):
                worker_ip = get_system_ip()

                # Remove only the current worker from the saved list
                worker_ips = load_worker_ips()
                if worker_ip in worker_ips:
                    worker_ips.remove(worker_ip)
                    save_worker_ips(worker_ips)

                subprocess.call("taskkill /F /IM locust.exe", shell=True)  # Only for Windows
                st.success("Worker stopped successfully!")
