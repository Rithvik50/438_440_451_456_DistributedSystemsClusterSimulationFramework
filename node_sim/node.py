import json
import os
import time
import requests
import sys
import signal
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NodeSimulator:
    def __init__(self):
        self.node_id = os.environ.get("NODE_ID")
        self.api_server = os.environ.get("API_SERVER")
        self.cpu_cores = int(os.environ.get("CPU_CORES", "2"))  # Default to 2 cores
        self.pods = []
        self.running = True
        
        if not self.node_id or not self.api_server:
            logger.error("NODE_ID and API_SERVER environment variables must be set")
            sys.exit(1)
            
        # Register signal handlers
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
    
    def handle_shutdown(self, signum, frame):
        logger.info("Shutting down node simulator...")
        self.running = False
    
    def run(self):
        consecutive_failures = 0
        max_failures = 3
        
        while self.running:
            try:
                # Log the API server URL we're trying to connect to
                logger.info(f"Attempting to send heartbeat to {self.api_server}")
                
                # Prepare heartbeat data
                heartbeat_data = {
                    "nodeId": self.node_id,
                    "status": "Healthy",
                    "pods": self.pods,
                    "cpuCores": self.cpu_cores
                }
                
                # Send heartbeat to API server with retry
                for attempt in range(3):
                    try:
                        response = requests.post(
                            f"{self.api_server}/heartbeat",
                            json=heartbeat_data,
                            timeout=5
                        )
                        
                        if response.status_code == 200:
                            # Reset failure count on success
                            consecutive_failures = 0
                            # Update pods from response
                            response_data = response.json()
                            self.pods = response_data.get("pods", [])
                            logger.info(f"Node {self.node_id} heartbeat successful. Pods: {self.pods}")
                            break
                        else:
                            logger.error(f"Failed to send heartbeat (attempt {attempt + 1}): {response.status_code}")
                            if attempt < 2:  # Don't sleep on the last attempt
                                time.sleep(1)
                    except requests.exceptions.RequestException as e:
                        logger.error(f"Network error (attempt {attempt + 1}): {e}")
                        if attempt < 2:  # Don't sleep on the last attempt
                            time.sleep(1)
                
                if response.status_code != 200:
                    consecutive_failures += 1
                    logger.error(f"All heartbeat attempts failed for node {self.node_id}")
                    
            except Exception as e:
                consecutive_failures += 1
                logger.error(f"Unexpected error in heartbeat loop: {e}")
            
            # Check if we've had too many consecutive failures
            if consecutive_failures >= max_failures:
                logger.error(f"Too many consecutive failures ({consecutive_failures}). Shutting down node.")
                self.running = False
                break
            
            # Wait before next heartbeat
            time.sleep(5)

def main():
    node = NodeSimulator()
    node.run()

if __name__ == "__main__":
    main() 