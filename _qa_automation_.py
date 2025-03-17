import streamlit as st
import os
import subprocess
import socket
import json


STATUS_FILE = "master_status.json"


# Custom CSS for info icon and tooltip
st.markdown("""
<style>
/* Info icon style */
.info-icon {
    font-size: 16px;
    color: #1E90FF;
    cursor: pointer;
    margin-left: 5px;
}

/* Tooltip style */
.tooltip {
    position: relative;
    display: inline-block;
}

.tooltip .tooltiptext {
    visibility: hidden;
    width: 300px;
    background-color: #f9f9f9;
    color: #000;
    text-align: left;
    border-radius: 5px;
    padding: 10px;
    position: absolute;
    z-index: 1;
    bottom: 125%; /* Position above the icon */
    left: 50%;
    margin-left: -150px; /* Center the tooltip */
    opacity: 0;
    transition: opacity 0.3s;
    border: 1px solid #ddd;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}

.tooltip:hover .tooltiptext {
    visibility: visible;
    opacity: 1;
}
</style>
""", unsafe_allow_html=True)

def qa_automation_page():
    """
    Main Page for QA Automation - Aligned with STLC Cycle
    """
    st.header("?? QA Automation")

    # Define STLC phases in sequence
    stlc_phase = st.selectbox(
        "Select Phase:",
        [
            "Requirement Analysis",
            "Test Planning",
            "Test Case Development",
            "Test Environment Setup",
            "Test Execution",
            "Test Closure"
        ]
    )

    # Handle the selected STLC phase
    if stlc_phase == "Requirement Analysis":
        st.write("### Requirement Analysis")
        st.markdown("""
        <div class="tooltip">
            <span class="info-icon"></span>
            <span class="tooltiptext">
                <b>Purpose:</b> Understand and analyze the testing requirements.<br>
                <b>Activities:</b><br>
                - Review software requirements specifications (SRS).<br>
                - Identify testable requirements.<br>
                - Define the scope of testing.
            </span>
        </div>
        """, unsafe_allow_html=True)
        # Placeholder for requirement analysis functionality
        st.info("Requirement analysis features will be added soon.")

    elif stlc_phase == "Test Planning":
        st.write("### Test Planning")
        st.markdown("""
        <div class="tooltip">
            <span class="info-icon"></span>
            <span class="tooltiptext">
                <b>Purpose:</b> Define the test strategy, scope, resources, and schedule.<br>
                <b>Activities:</b><br>
                - Prepare a test plan document.<br>
                - Allocate resources (team, tools, environment).<br>
                - Define the test schedule and milestones.
            </span>
        </div>
        """, unsafe_allow_html=True)
        # Placeholder for test planning functionality
        st.info("Test planning features will be added soon.")

    elif stlc_phase == "Test Case Development":
        st.write("### Test Case Development")
        st.markdown("""
        <div class="tooltip">
            <span class="info-icon"></span>
            <span class="tooltiptext">
                <b>Purpose:</b> Create detailed test cases and test scripts.<br>
                <b>Activities:</b><br>
                - Write test cases based on requirements.<br>
                - Review and approve test cases.<br>
                - Prepare test data and scripts.
            </span>
        </div>
        """, unsafe_allow_html=True)
        # Placeholder for test case development functionality
        st.info("Test case development features will be added soon.")

    elif stlc_phase == "Test Environment Setup":
        st.write("### Test Environment Setup")
        st.markdown("""
        <div class="tooltip">
            <span class="info-icon"></span>
            <span class="tooltiptext">
                <b>Purpose:</b> Set up the hardware, software, and network for testing.<br>
                <b>Activities:</b><br>
                - Configure test servers and databases.<br>
                - Install necessary software and tools.<br>
                - Verify the test environment is ready.
            </span>
        </div>
        """, unsafe_allow_html=True)
        # Placeholder for test environment setup functionality
        st.info("Test environment setup features will be added soon.")

    elif stlc_phase == "Test Execution":
        st.write("### Test Execution")
        st.markdown("""
        <div class="tooltip">
            <span class="info-icon"></span>
            <span class="tooltiptext">
                <b>Purpose:</b> Execute test cases and report defects.<br>
                <b>Activities:</b><br>
                - Run test cases and record results.<br>
                - Log defects in a tracking tool.<br>
                - Retest fixed defects.
            </span>
        </div>
        """, unsafe_allow_html=True)
        # Integrate Load Testing functionality here
        unit_testing_page()

    elif stlc_phase == "Test Closure":
        st.write("### Test Closure")
        st.markdown("""
        <div class="tooltip">
            <span class="info-icon"></span>
            <span class="tooltiptext">
                <b>Purpose:</b> Analyze test results, prepare reports, and archive test artifacts.<br>
                <b>Activities:</b><br>
                - Prepare a test summary report.<br>
                - Document lessons learned.<br>
                - Archive test cases, scripts, and results.
            </span>
        </div>
        """, unsafe_allow_html=True)
        # Placeholder for test closure functionality
        st.info("Test closure features will be added soon.")



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


def unit_testing_page():
    logged_in_user = st.session_state.username
    is_superadmin = logged_in_user == "superadmin"

    # Set mode based on user type
    if is_superadmin:
        mode = "Master"
        st.session_state["is_master_running"] = False  # Track Master status
    else:
        mode = "Worker"

    st.write(f"### {mode} Load Configuration  - {logged_in_user}")

    UPLOADS_FOLDER = "uploads"
    os.makedirs(UPLOADS_FOLDER, exist_ok=True)

    # Function to get system IP
    def get_system_ip():
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception as e:
            st.error(f"Failed to fetch system IP: {e}")
            return "localhost"

    # Function to list available .py files
    def get_locust_files():
        return [f for f in os.listdir(UPLOADS_FOLDER) if f.endswith(".py")]

    # Function to create and execute .bat files
    def create_bat_file(mode, master_ip, locust_file, host):
        bat_filename = f"{mode.lower()}.bat"
        locust_file_path = os.path.join(UPLOADS_FOLDER, locust_file)
        
        bat_content = (
            f"@echo off\n"
            f"echo Starting Locust in {mode} Mode...\n"
            f"locust -f {locust_file_path} --host={host} "
        )
        
        if mode == "Master":
            bat_content += "--web-port 8088 --master\n"
        else:
            bat_content += f"--worker --master-host={master_ip}\n"
        
        bat_content += "pause"
        
        bat_path = os.path.join(os.getcwd(), bat_filename)
        with open(bat_path, "w") as f:
            f.write(bat_content)
        
        return bat_path

    
    # Master Mode (Only for Superadmin)
    if is_superadmin:
        locust_files = get_locust_files()
        master_ip = get_system_ip()
        status = load_master_status()

        st.write(f"Detected Master IP: `{master_ip}`")

        if locust_files:
            selected_file = st.selectbox("Select Locust Test File", locust_files)
            st.markdown("**Files is attached. Click on start!**")
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
            st.success("Master stopped!")
            st.markdown("**All Workers should disconnect!**")


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
            bat_file_path = create_bat_file("Worker", master_ip, selected_file, "http://localhost")
            subprocess.Popen(bat_file_path, shell=True)
            st.success("Worker started successfully!")

        if st.button("Stop Worker"):
            subprocess.call("taskkill /F /IM locust.exe", shell=True)
            st.success("Worker stopped!")
