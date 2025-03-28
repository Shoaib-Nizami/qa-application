import subprocess

# Global variables
worker_processes = []

def run_locust_worker(script_path, master_host, worker_nodes):
    """
    Runs Locust in Worker mode.
    """
    global worker_processes

    for i in range(worker_nodes):
        command = [
            "locust",
            "-f", script_path,
            "--worker",
            "--master-host", master_host,
        ]

        worker_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        worker_processes.append(worker_process)

def stop_locust():
    """Stops the Locust Worker processes."""
    global worker_processes

    # Stop all worker processes (if running)
    for worker in worker_processes:
        worker.terminate()
        worker.wait()  # Ensure the process is fully terminated
    worker_processes = []  # Clear the list of worker processes