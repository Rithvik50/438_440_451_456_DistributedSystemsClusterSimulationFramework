import argparse
import json
import requests
import sys

API_BASE_URL = "http://localhost:8080"

def add_node(cpu_cores):
    try:
        response = requests.post(
            f"{API_BASE_URL}/nodes",
            json={"cpuCores": cpu_cores},
            timeout=10
        )
        
        if response.status_code == 201:
            print(response.text)
        else:
            print(f"Failed to add node, status: {response.status_code}")
            print(response.text)
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def stop_node(node_id):
    try:
        response = requests.post(
            f"{API_BASE_URL}/nodes/{node_id}/stop",
            timeout=10
        )
        
        if response.status_code == 200:
            print("Node stopped successfully")
        else:
            print(f"Failed to stop node: {response.text}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def delete_node(node_id):
    try:
        response = requests.delete(
            f"{API_BASE_URL}/nodes/{node_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            print("Node deleted successfully")
        else:
            print(f"Failed to delete node: {response.text}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def launch_pod(cpu_required):
    try:
        response = requests.post(
            f"{API_BASE_URL}/pods",
            json={"cpuRequired": cpu_required},
            timeout=10
        )
        
        if response.status_code == 201:
            print("Pod launched successfully")
        else:
            print(f"Failed to launch pod, status: {response.status_code}")
            print(response.text)
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def list_nodes():
    try:
        response = requests.get(
            f"{API_BASE_URL}/nodes",
            timeout=10
        )
        
        if response.status_code == 200:
            nodes = response.json()
            for node_id, node in nodes.items():
                print(f"Node {node_id}: CPU {node['available_cpu']}/{node['cpu_cores']}, "
                      f"Status: {node['health_status']}, Pods: {node['pods']}")
        else:
            print(f"Failed to list nodes: {response.text}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Kube-Sim CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Add node command
    add_node_parser = subparsers.add_parser("add-node", help="Add a new node with specified CPU cores")
    add_node_parser.add_argument("cpuCores", type=int, help="Number of CPU cores")
    
    # Stop node command
    stop_node_parser = subparsers.add_parser("stop-node", help="Stop a node")
    stop_node_parser.add_argument("nodeID", help="Node ID")
    
    # Delete node command
    delete_node_parser = subparsers.add_parser("delete-node", help="Delete a stopped node")
    delete_node_parser.add_argument("nodeID", help="Node ID")
    
    # Launch pod command
    launch_pod_parser = subparsers.add_parser("launch-pod", help="Launch a pod with specified CPU requirements")
    launch_pod_parser.add_argument("cpuRequired", type=int, help="CPU required")
    
    # List nodes command
    subparsers.add_parser("list-nodes", help="List all nodes with their health status")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == "add-node":
        add_node(args.cpuCores)
    elif args.command == "stop-node":
        stop_node(args.nodeID)
    elif args.command == "delete-node":
        delete_node(args.nodeID)
    elif args.command == "launch-pod":
        launch_pod(args.cpuRequired)
    elif args.command == "list-nodes":
        list_nodes()

if __name__ == "__main__":
    main() 
    