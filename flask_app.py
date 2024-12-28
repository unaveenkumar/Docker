from flask import Flask, render_template, jsonify
import docker
import psutil
import time

app = Flask(__name__)

def get_docker_version():
    """
    Retrieve the Docker version details.
    """
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
        return {"error": str(e)}

def get_running_containers():
    """
    Retrieve the list of running Docker containers.
    """
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
        return {"error": str(e)}

@app.route("/")
def home():
    """
    Render the homepage with Docker details and graphs.
    """
    version_info = get_docker_version()
    containers = get_running_containers()
    return render_template("index.html", version_info=version_info, containers=containers)

@app.route("/system-stats")
def system_stats():
    """
    Endpoint to provide real-time system stats for CPU and network usage.
    """
    cpu_percent = psutil.cpu_percent(interval=1)
    net_io = psutil.net_io_counters()
    stats = {
        "cpu_percent": cpu_percent,
        "sent": net_io.bytes_sent,
        "recv": net_io.bytes_recv,
        "timestamp": time.time(),
    }
    return jsonify(stats)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
