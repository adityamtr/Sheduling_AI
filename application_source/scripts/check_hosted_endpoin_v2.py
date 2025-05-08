import requests
import time
import subprocess
import os
import signal
import psutil  # install with: pip install psutil

# Configuration
TUNNEL_URL = "https://hostedqwen25mark1.loca.lt"
CHECK_INTERVAL = 15 * 60  # seconds
PORT = "9000"
SUBDOMAIN = "hostedqwen25mark1"

def is_tunnel_healthy(url):
    try:
        response = requests.get(url, timeout=200)
        return response.status_code == 200
    except requests.RequestException:
        return False

def kill_existing_lt_processes():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        cmdline = proc.info.get('cmdline')
        if cmdline and any('lt' in part or 'localtunnel' in part for part in cmdline):
            print(f"Terminating existing lt process: PID {proc.pid}")
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                try:
                    proc.kill()
                except Exception as e:
                    print(f"Failed to force kill process {proc.pid}: {e}")

def restart_tunnel():
    print("Restarting LocalTunnel...")
    command = f"lt --port {PORT} --subdomain {SUBDOMAIN}"
    subprocess.Popen(["cmd", "/c", command], creationflags=subprocess.CREATE_NEW_CONSOLE)

while True:
    print(f"[Health Check] Checking {TUNNEL_URL}...")
    if is_tunnel_healthy(TUNNEL_URL):
        print("✅ Tunnel is healthy.")
    else:
        print("❌ Tunnel is down. Restarting...")
        kill_existing_lt_processes()
        restart_tunnel()
    time.sleep(CHECK_INTERVAL)
