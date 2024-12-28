from flask import Flask, request, render_template, jsonify
import docker
import psutil
import time
import os
import boto3
import logging
import subprocess

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def log_request():
    logging.info(f"Request: {request.method} {request.path} - IP: {request.remote_addr}")

def get_docker_version():
    try:
        client = docker.from_env()
        version_info = client.version()
        return {
            "Version": version_info.get("Version", "N/A"),
            "API Version": version_info.get("ApiVersion", "N/A"),
            "Go Version": version_info.get("GoVersion", "N/A"),
            "Git Commit": version_info.get("GitCommit", "N/A"),
            "OS/Arch": f"{version_info.get('Os', 'N/A')}/{version_info.get('Arch', 'N/A')}",
        }
    except Exception as e:
        logging.error(f"Docker version retrieval error: {e}")
        return {"error": str(e)}

def get_running_containers():
    try:
        client = docker.from_env()
        containers = client.containers.list()
        container_list = [
            {
                "id": container.id[:12],
                "name": container.name,
                "image": ", ".join(container.image.tags) if container.image.tags else "No tag",
                "status": container.status,
            }
            for container in containers
        ]
        return container_list
    except Exception as e:
        logging.error(f"Error retrieving running containers: {e}")
        return {"error": str(e)}

def get_ec2_metadata():
    try:
        ec2 = boto3.client("ec2")
        instance_id = os.popen("curl -s http://169.254.169.254/latest/meta-data/instance-id").read()
        region = os.popen("curl -s http://169.254.169.254/latest/meta-data/placement/region").read()
        instance_info = ec2.describe_instances(InstanceIds=[instance_id])
        tags = instance_info["Reservations"][0]["Instances"][0].get("Tags", [])
        instance_type = instance_info["Reservations"][0]["Instances"][0]["InstanceType"]
        return {
            "instance_id": instance_id,
            "region": region,
            "instance_type": instance_type,
            "tags": tags,
        }
    except Exception as e:
        logging.error(f"Error retrieving EC2 metadata: {e}")
        return {"error": str(e)}

def get_open_ports():
    try:
        connections = psutil.net_connections()
        open_ports = [
            {
                "local_address": f"{conn.laddr.ip}:{conn.laddr.port}",
                "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A",
                "status": conn.status,
                "pid": conn.pid,
            }
            for conn in connections if conn.status == "LISTEN"
        ]
        return open_ports
    except Exception as e:
        logging.error(f"Error retrieving open ports: {e}")
        return {"error": str(e)}

def get_last_logged_in_user():
    try:
        last_login = subprocess.check_output("last -n 1", shell=True).decode().strip()
        return {"last_login": last_login}
    except Exception as e:
        logging.error(f"Error retrieving last logged-in user: {e}")
        return {"error": str(e)}

@app.route("/")
def home():
    log_request()
    version_info = get_docker_version()
    containers = get_running_containers()
    ec2_info = get_ec2_metadata()
    open_ports = get_open_ports()
    last_login = get_last_logged_in_user()
    return render_template(
        "index.html",
        version_info=version_info,
        containers=containers,
        ec2_info=ec2_info,
        open_ports=open_ports,
        last_login=last_login,
    )

@app.route("/system-stats")
def system_stats():
    log_request()
    cpu_percent = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    net_io = psutil.net_io_counters()
    stats = {
        "cpu_percent": cpu_percent,
        "memory_used": memory_info.used,
        "memory_total": memory_info.total,
        "sent": net_io.bytes_sent,
        "recv": net_io.bytes_recv,
        "timestamp": time.time(),
    }
    return jsonify(stats)

@app.route("/logs")
def view_logs():
    log_request()
    try:
        with open("app.log", "r") as log_file:
            logs = log_file.readlines()
        return jsonify({"logs": logs})
    except Exception as e:
        logging.error(f"Error reading logs: {e}")
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
