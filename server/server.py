from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import logging
import subprocess
import threading
import time
import uuid
import socket

logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

def get_host_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

HOST_IP = get_host_ip()

nodes = {}
pods = {}
nodes_lock = threading.Lock()
pods_lock = threading.Lock()
scheduler = "first-fit"

class Node:
    def __init__(self, id, cpu_cores):
        self.id = id
        self.cpu_cores = cpu_cores
        self.available_cpu = cpu_cores
        self.pods = []
        self.health_status = "Healthy"
        self.last_heartbeat = time.time()
        self.heartbeat_count = 0
        self.is_running = True

class Pod:
    def __init__(self, id, cpu_required, node_id):
        self.id = id
        self.cpu_required = cpu_required
        self.node_id = node_id
        self.status = "Running"
        self.created_at = time.time()
        self.last_updated = time.time()
        self.health_status = "Healthy"

@app.route('/nodes', methods=['GET'])
def get_nodes():
    with nodes_lock:
        return jsonify({k: v.__dict__ for k, v in nodes.items()})

@app.route('/nodes', methods=['POST'])
def add_node():
    try:
        data = request.get_json()
        cpu_cores = data.get('cpuCores', 0)
        
        if cpu_cores <= 0:
            return jsonify({"error": "CPU cores must be positive"}), 400
        
        node_id = str(uuid.uuid4())
        
        with nodes_lock:
            nodes[node_id] = Node(node_id, cpu_cores)
        
        cmd = [
            "docker", "run", "-d",
            "--name", node_id,
            "-e", f"NODE_ID={node_id}",
            "-e", f"CPU_CORES={cpu_cores}",
            "-e", f"API_SERVER=http://{HOST_IP}:8080",
            "--network", "host",
            "kube-sim-node"
        ]
        
        logger.info(f"Launching node container with command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            with nodes_lock:
                del nodes[node_id]
            logger.error(f"Failed to launch node container: {result.stderr}")
            return jsonify({"error": "Failed to launch node"}), 500
        
        time.sleep(2)
        cmd = ["docker", "inspect", "-f", "{{.State.Running}}", node_id]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0 or result.stdout.strip() != "true":
            with nodes_lock:
                del nodes[node_id]
            logger.error(f"Container failed to start properly: {result.stderr}")
            return jsonify({"error": "Container failed to start"}), 500
        
        logger.info(f"Node {node_id} added with {cpu_cores} CPU cores")
        return jsonify({"message": f"Node {node_id} added with {cpu_cores} CPU cores"}), 201
        
    except Exception as e:
        logger.error(f"Error adding node: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/nodes/<node_id>/stop', methods=['POST'])
def stop_node(node_id):
    try:
        with nodes_lock:
            if node_id not in nodes:
                return jsonify({"error": "Node not found"}), 404
            
            node = nodes[node_id]
            node.is_running = False
            node.health_status = "Stopped"
            
            # Get pods that need to be rescheduled
            pods_to_reschedule = node.pods.copy()
            node.pods = []  # Clear pods from stopped node
            
            cmd = ["docker", "stop", node_id]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return jsonify({"error": "Failed to stop node container"}), 500
            
            # Try to reschedule pods to other healthy nodes
            with pods_lock:
                for pod_id in pods_to_reschedule:
                    pod = pods[pod_id]
                    rescheduled = False
                    
                    # Try to find a healthy node with enough CPU
                    for other_node_id, other_node in nodes.items():
                        if (other_node_id != node_id and 
                            other_node.health_status == "Healthy" and 
                            other_node.is_running and 
                            other_node.available_cpu >= pod.cpu_required):
                            # Move pod to new node
                            pod.node_id = other_node_id
                            pod.last_updated = time.time()
                            other_node.available_cpu -= pod.cpu_required
                            other_node.pods.append(pod_id)
                            rescheduled = True
                            logger.info(f"Pod {pod_id} rescheduled from node {node_id} to node {other_node_id}")
                            break
                    
                    # If pod couldn't be rescheduled, mark it as failed
                    if not rescheduled:
                        pod.status = "Failed"
                        pod.health_status = "Unhealthy"
                        logger.warning(f"Pod {pod_id} could not be rescheduled, marking as failed")
            
            logger.info(f"Node {node_id} stopped")
            return jsonify({"message": f"Node {node_id} stopped"}), 200
            
    except Exception as e:
        logger.error(f"Error stopping node: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/nodes/<node_id>/delete', methods=['DELETE'])
def delete_node(node_id):
    try:
        with nodes_lock:
            if node_id not in nodes:
                return jsonify({"error": "Node not found"}), 404
            
            del nodes[node_id]
            
            cmd = ["docker", "rm", "-f", node_id]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return jsonify({"error": "Failed to delete node container"}), 500
            
            logger.info(f"Node {node_id} deleted")
            return jsonify({"message": f"Node {node_id} deleted"}), 200
            
    except Exception as e:
        logger.error(f"Error deleting node: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/pods', methods=['POST'])
def launch_pod():
    try:
        data = request.get_json()
        cpu_required = data.get('cpuRequired', 0)
        
        if cpu_required <= 0:
            return jsonify({"error": "CPU required must be positive"}), 400
        
        # Find a suitable node
        with nodes_lock:
            for node_id, node in nodes.items():
                if (node.health_status == "Healthy" and 
                    node.is_running and 
                    node.available_cpu >= cpu_required):
                    pod_id = str(uuid.uuid4())
                    pods[pod_id] = Pod(pod_id, cpu_required, node_id)
                    node.available_cpu -= cpu_required
                    node.pods.append(pod_id)
                    return jsonify({"message": f"Pod {pod_id} launched on node {node_id}"}), 201
        
        return jsonify({"error": "No healthy nodes with sufficient CPU available"}), 400
        
    except Exception as e:
        logger.error(f"Error launching pod: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/heartbeat', methods=['POST'])
def handle_heartbeat():
    try:
        data = request.get_json()
        node_id = data.get('nodeId')
        cpu_cores = data.get('cpuCores', 0)
        
        with nodes_lock:
            if node_id in nodes:
                node = nodes[node_id]
                if node.is_running:
                    node.last_heartbeat = time.time()
                    node.heartbeat_count += 1
                    node.cpu_cores = cpu_cores
                    return jsonify({"message": "Heartbeat received", "pods": node.pods}), 200
                else:
                    return jsonify({"error": "Node is stopped"}), 403
        
        return jsonify({"error": "Node not found"}), 404
        
    except Exception as e:
        logger.error(f"Error handling heartbeat: {e}")
        return jsonify({"error": str(e)}), 500

def health_monitor():
    while True:
        time.sleep(5)
        current_time = time.time()
        
        with nodes_lock:
            for node_id, node in nodes.items():
                if node.is_running:
                    time_since_heartbeat = current_time - node.last_heartbeat
                    if time_since_heartbeat > 15:
                        cmd = ["docker", "inspect", "-f", "{{.State.Running}} {{.State.Status}}", node_id]
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        
                        if result.returncode == 0:
                            status = result.stdout.strip().split()
                            if len(status) == 2:
                                is_running, container_status = status
                                logger.warning(f"Node {node_id} status: Running={is_running}, Status={container_status}, Time since heartbeat: {time_since_heartbeat:.2f}s")
                                
                                if is_running == "true":
                                    logger.warning(f"Container for node {node_id} is running but not sending heartbeats")
                                else:
                                    logger.warning(f"Container for node {node_id} is not running (status: {container_status})")
                                    node.health_status = "Failed"
                                    reschedule_pods(node_id)
                        else:
                            logger.error(f"Failed to inspect container {node_id}: {result.stderr}")
                            node.health_status = "Failed"
                            reschedule_pods(node_id)

def reschedule_pods(failed_node_id):
    """Reschedule pods from a failed node to healthy nodes"""
    with pods_lock:
        pods_to_reschedule = [pod_id for pod_id, pod in pods.items() if pod.node_id == failed_node_id]
        
        for pod_id in pods_to_reschedule:
            pod = pods[pod_id]
            with nodes_lock:
                for node_id, node in nodes.items():
                    if (node.health_status == "Healthy" and 
                        node.is_running and 
                        node.available_cpu >= pod.cpu_required):
                        pod.node_id = node_id
                        pod.last_updated = time.time()
                        node.available_cpu -= pod.cpu_required
                        node.pods.append(pod_id)
                        logger.info(f"Pod {pod_id} rescheduled from node {failed_node_id} to node {node_id}")
                        break
                else:
                    pod.status = "Failed"
                    pod.health_status = "Unhealthy"
                    logger.warning(f"Could not reschedule pod {pod_id}, no healthy nodes with sufficient CPU available")

@app.route('/pods/<pod_id>', methods=['DELETE'])
def delete_pod(pod_id):
    try:
        with pods_lock:
            if pod_id not in pods:
                return jsonify({"error": "Pod not found"}), 404
            
            pod = pods[pod_id]
            
            with nodes_lock:
                if pod.node_id in nodes:
                    node = nodes[pod.node_id]
                    node.available_cpu += pod.cpu_required
                    node.pods.remove(pod_id)
            
            del pods[pod_id]
            
            logger.info(f"Pod {pod_id} deleted")
            return jsonify({"message": f"Pod {pod_id} deleted"}), 200
            
    except Exception as e:
        logger.error(f"Error deleting pod: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/pods', methods=['GET'])
def list_pods():
    try:
        with pods_lock:
            pods_list = []
            for pod_id, pod in pods.items():
                pods_list.append({
                    "id": pod_id,
                    "cpu_required": pod.cpu_required,
                    "node_id": pod.node_id,
                    "status": pod.status,
                    "health_status": pod.health_status,
                    "created_at": pod.created_at,
                    "last_updated": pod.last_updated
                })
            return jsonify(pods_list), 200
    except Exception as e:
        logger.error(f"Error listing pods: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    monitor_thread = threading.Thread(target=health_monitor, daemon=True)
    monitor_thread.start()
    
    app.run(host='0.0.0.0', port=8080, debug=True)