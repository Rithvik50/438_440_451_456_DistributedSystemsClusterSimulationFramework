# Kube-Sim: Distributed Systems Cluster Simulation Framework

A lightweight, simulation-based distributed system that mimics core Kubernetes cluster management functionalities. Built for educational purposes to demonstrate key distributed computing concepts.

## Project Structure

```
.
├── README.md
├── cli.py                 # Python CLI for cluster management
├── node_sim/             # Node simulator implementation
│   ├── Dockerfile        # Docker configuration for node simulator
│   ├── node.py          # Node simulator implementation
│   └── requirements.txt  # Python dependencies
├── server/              # API server implementation
│   ├── Dockerfile       # Docker configuration for server
│   └── server.py        # Python server implementation
└── web/                # Web interface
    ├── index.html      # Dashboard HTML
    ├── style.css       # Dashboard styles
    └── script.js       # Dashboard JavaScript with Chart.js visualization
```

## Prerequisites

- Docker
- Python 3.9+
- Web browser with JavaScript enabled

## Setup and Running

### 1. Start the API Server

```bash
cd server
python server.py
```

### 2. Start a Node Simulator

```bash
cd node_sim
docker build -t kube-sim-node .
# The node ID and CPU cores will be automatically assigned when adding nodes through CLI or web interface
```

### 3. Access the Web Interface

```bash
cd web
python -m http.server 3000
```
Then open `http://localhost:3000` in your browser

### 4. Using the CLI

```bash
# Add a node with 2 CPU cores
python cli.py add-node 2

# List all nodes
python cli.py list-nodes

# Launch a pod requiring 1 CPU
python cli.py launch-pod 1

# Stop a node
python cli.py stop-node <node_id>

# Delete a node
python cli.py delete-node <node_id>
```

## Architecture

### Components

1. **API Server** (`server/server.py`):
   - Manages nodes and pods
   - Handles scheduling using first-fit algorithm
   - Monitors node health through heartbeats
   - Implements automatic pod rescheduling on node failures

2. **Node Simulator** (`node_sim/node.py`):
   - Simulates a cluster node in a Docker container
   - Sends regular heartbeats to the API server
   - Reports CPU usage and health status
   - Handles graceful shutdown

3. **CLI** (`cli.py`):
   - Command-line interface for cluster management
   - Supports node and pod operations
   - Provides status monitoring capabilities

4. **Web Interface** (`web/`):
   - Real-time cluster visualization
   - Interactive node and pod management
   - Live heartbeat monitoring with visual graph
   - Responsive design for better user experience

## Features

- Dynamic node registration and management
- Real-time health monitoring with visual heartbeat display
- Pod scheduling with CPU resource management
- Automatic pod rescheduling on node failures
- Interactive web dashboard
- Command-line interface for automation
- Docker-based node simulation
- Graceful node shutdown and cleanup

## Health Monitoring

The system implements a comprehensive health monitoring system:
- Nodes send regular heartbeats to the server
- Server monitors node health status
- Visual heartbeat display in the web interface
- Automatic detection and handling of node failures
- Pod rescheduling when nodes become unhealthy

## Resource Management

- CPU-based scheduling
- First-fit pod placement algorithm
- Resource tracking per node
- Automatic resource reallocation on node failure

## Error Handling

- Graceful node failure detection
- Automatic pod rescheduling
- Container cleanup on node deletion
- Comprehensive error reporting
- User-friendly error messages in both CLI and web interface
