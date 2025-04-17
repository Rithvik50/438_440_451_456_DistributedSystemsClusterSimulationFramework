const API_BASE_URL = "http://localhost:8080";

// Store charts for each node
const nodeCharts = {};

function createHeartbeatChart(nodeId) {
    const canvas = document.createElement('canvas');
    canvas.className = 'heartbeat-chart';
    
    // Create a simple heartbeat pattern with sharp peaks
    const generateECGData = () => {
        const data = [];
        const points = 100;
        
        for (let i = 0; i < points; i++) {
            data.push(0.5); // Flat baseline
        }
        return data;
    };
    
    const data = {
        labels: Array(100).fill(''),
        datasets: [{
            data: generateECGData(),
            borderColor: '#28a745',
            backgroundColor: 'rgba(40, 167, 69, 0.1)',
            tension: 0,
            pointRadius: 0,
            borderWidth: 2,
            fill: true
        }]
    };

    const config = {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 0
            },
            scales: {
                y: {
                    display: false,
                    beginAtZero: true,
                    min: 0.4,
                    max: 1.1
                },
                x: {
                    display: false
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: false
                }
            }
        }
    };

    const chart = new Chart(canvas, config);
    nodeCharts[nodeId] = { 
        chart, 
        data,
        position: 0 // Add position tracker for continuous movement
    };
    return canvas;
}

function updateHeartbeatGraph(nodeId, isActive) {
    if (!nodeCharts[nodeId]) return;

    const { chart, data, position } = nodeCharts[nodeId];
    
    if (isActive) {
        const newData = Array(100).fill(0.5);
        
        // Create the heartbeat pattern
        const createHeartbeat = (startPosition) => {
            // Only draw the heartbeat if it would be visible
            if (startPosition >= 0 && startPosition < 100) {
                newData[startPosition] = 0.5;     // Start at baseline
                newData[startPosition + 1] = 1.0;  // Sharp up
                newData[startPosition + 2] = 0.6;  // First down
                newData[startPosition + 3] = 0.5;  // Back to baseline
            }
        };

        // Add heartbeats based on the current position
        createHeartbeat(position);
        createHeartbeat(position + 25);
        createHeartbeat(position + 50);
        createHeartbeat(position + 75);

        // Update position for next frame
        nodeCharts[nodeId].position = (position + 1) % 25;
        
        data.datasets[0].data = newData;
    } else {
        // Show flat line when inactive
        data.datasets[0].data = Array(100).fill(0.5);
    }
    
    chart.update('none');
}

// Update statistics
function updateStats(nodes) {
    const totalNodes = Object.keys(nodes).length;
    const totalPods = Object.values(nodes).reduce((sum, node) => sum + node.pods.length, 0);
    
    document.getElementById('totalNodes').textContent = totalNodes;
    document.getElementById('totalPods').textContent = totalPods;
}

async function fetchNodes() {
    try {
        const response = await fetch(`${API_BASE_URL}/nodes`);
        const nodes = await response.json();
        displayNodes(nodes);
        updateStats(nodes);
    } catch (error) {
        console.error('Error fetching nodes:', error);
    }
}

// Add function to fetch pod details
async function fetchPods() {
    try {
        const response = await fetch(`${API_BASE_URL}/pods`);
        return await response.json();
    } catch (error) {
        console.error('Error fetching pods:', error);
        return [];
    }
}

// Update displayNodes to include pod details
async function displayNodes(nodes) {
    const nodesContainer = document.getElementById('nodes');
    nodesContainer.innerHTML = '';

    // Fetch pod details
    const pods = await fetchPods();
    const podsMap = {};
    pods.forEach(pod => {
        podsMap[pod.id] = pod;
    });

    Object.entries(nodes).forEach(([id, node]) => {
        const nodeElement = document.createElement('div');
        nodeElement.className = `node ${node.health_status.toLowerCase()}`;
        nodeElement.setAttribute('data-node-id', id);
        
        // Calculate time since last heartbeat
        const lastHeartbeat = new Date(node.last_heartbeat * 1000);
        const timeSinceHeartbeat = Math.floor((Date.now() - lastHeartbeat) / 1000);
        const isActive = timeSinceHeartbeat < 20;
        const heartbeatClass = isActive ? 'heartbeat-active' : 'heartbeat-inactive';
        
        // Create heartbeat monitor
        const heartbeatMonitor = document.createElement('div');
        heartbeatMonitor.className = 'heartbeat-monitor';
        heartbeatMonitor.appendChild(createHeartbeatChart(id));
        
        // Update heartbeat graph
        updateHeartbeatGraph(id, isActive);
        
        // Create pods list with detailed information
        const podsList = node.pods.map(podId => {
            const pod = podsMap[podId];
            if (!pod) return '';

            const podStatus = pod.status === "Running" ? "pod-running" : "pod-failed";
            const rescheduledInfo = pod.last_updated > pod.created_at ? 
                `<span class="pod-rescheduled">Rescheduled</span>` : '';
            
            return `
                <div class="pod-item ${podStatus}">
                    <div class="pod-info">
                        <span>Pod ${podId.substring(0, 8)}</span>
                        ${rescheduledInfo}
                        <span class="pod-details">CPU: ${pod.cpu_required}</span>
                        <span class="pod-status">Status: ${pod.health_status}</span>
                    </div>
                    <button onclick="deletePod('${podId}')" class="delete-btn">Delete</button>
                </div>
            `;
        }).join('');
        
        nodeElement.innerHTML = `
            <h3>Node ${id.substring(0, 8)}</h3>
            <div class="node-info">
                <div class="info-item">
                    <strong>CPU</strong>
                    <span>${node.available_cpu}/${node.cpu_cores}</span>
                </div>
                <div class="info-item">
                    <strong>Status</strong>
                    <span>${node.health_status}</span>
                </div>
                <div class="info-item">
                    <strong>Heartbeat</strong>
                    <span class="${heartbeatClass}">${isActive ? 'Active' : 'Inactive'}</span>
                </div>
                <div class="info-item">
                    <strong>Pods</strong>
                    <span>${node.pods.length}</span>
                </div>
            </div>
            <div class="pods-container">
                <h4>Running Pods</h4>
                ${podsList}
            </div>
            <div class="node-controls">
                <button onclick="stopNode('${id}')" class="stop-btn" ${!node.is_running ? 'disabled' : ''}>Stop</button>
                <button onclick="deleteNode('${id}')" class="delete-btn">Delete</button>
            </div>
        `;
        
        // Add heartbeat monitor
        nodeElement.appendChild(heartbeatMonitor);
        nodesContainer.appendChild(nodeElement);
    });
}

async function addNode() {
    const cpuCores = document.getElementById('cpuCores').value;
    if (!cpuCores) {
        alert('Please enter CPU cores');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/nodes`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ cpuCores: parseInt(cpuCores) }),
        });

        if (response.ok) {
            const result = await response.json();
            document.getElementById('cpuCores').value = '';
            alert(`Node added successfully: ${result.message}`);
            fetchNodes();
        } else {
            const error = await response.json();
            alert(`Failed to add node: ${error.error || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error adding node:', error);
        alert('Failed to add node. Please check if the server is running.');
    }
}

async function stopNode(nodeId) {
    try {
        const response = await fetch(`${API_BASE_URL}/nodes/${nodeId}/stop`, {
            method: 'POST',
        });

        if (response.ok) {
            alert(`Node ${nodeId} stopped successfully`);
            fetchNodes();
        } else {
            const error = await response.json();
            alert(`Failed to stop node: ${error.error || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error stopping node:', error);
        alert('Failed to stop node');
    }
}

async function deleteNode(nodeId) {
    if (!confirm(`Are you sure you want to delete node ${nodeId}?`)) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/nodes/${nodeId}/delete`, {
            method: 'DELETE',
        });

        if (response.ok) {
            alert(`Node ${nodeId} deleted successfully`);
            fetchNodes();
        } else {
            const error = await response.json();
            alert(`Failed to delete node: ${error.error || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error deleting node:', error);
        alert('Failed to delete node');
    }
}

async function launchPod() {
    const cpuRequired = document.getElementById('cpuRequired').value;
    if (!cpuRequired) {
        alert('Please enter CPU required');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/pods`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ cpuRequired: parseInt(cpuRequired) }),
        });

        if (response.ok) {
            document.getElementById('cpuRequired').value = '';
            fetchNodes();
        } else {
            const error = await response.json();
            alert(`Failed to launch pod: ${error.error}`);
        }
    } catch (error) {
        console.error('Error launching pod:', error);
        alert('Failed to launch pod');
    }
}

async function deletePod(podId) {
    if (!confirm(`Are you sure you want to delete pod ${podId}?`)) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/pods/${podId}`, {
            method: 'DELETE',
        });

        if (response.ok) {
            alert(`Pod ${podId} deleted successfully`);
            fetchNodes();
        } else {
            const error = await response.json();
            alert(`Failed to delete pod: ${error.error || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error deleting pod:', error);
        alert('Failed to delete pod');
    }
}

// Add function to fetch current scheduler
async function fetchScheduler() {
    try {
        const response = await fetch(`${API_BASE_URL}/scheduler`);
        const data = await response.json();
        document.getElementById('scheduler').value = data.scheduler;
    } catch (error) {
        console.error('Error fetching scheduler:', error);
    }
}

// Add function to change scheduler
async function changeScheduler() {
    const scheduler = document.getElementById('scheduler').value;
    try {
        const response = await fetch(`${API_BASE_URL}/scheduler`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ scheduler }),
        });

        if (response.ok) {
            const data = await response.json();
            alert(`Scheduling algorithm changed to ${data.scheduler}`);
        } else {
            const error = await response.json();
            alert(`Failed to change scheduler: ${error.error}`);
        }
    } catch (error) {
        console.error('Error changing scheduler:', error);
        alert('Failed to change scheduler');
    }
}

// Update the initial fetch to include scheduler
async function initialFetch() {
    await Promise.all([
        fetchNodes(),
        fetchScheduler()
    ]);
}

// Start periodic updates
setInterval(fetchNodes, 5000);
initialFetch(); // Initial fetch
