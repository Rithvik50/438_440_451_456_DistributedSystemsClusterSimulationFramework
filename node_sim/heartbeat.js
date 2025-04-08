const axios = require('axios');

const API_SERVER = 'http://host.docker.internal:3000'; // or your host machine IP

function startHeartbeat(nodeId) {
  setInterval(async () => {
    try {
      await axios.post(`${API_SERVER}/heartbeat`, { nodeId });
      console.log(`Heartbeat sent from ${nodeId}`);
    } catch (err) {
      console.error('Heartbeat failed:', err.message);
    }
  }, 5000); // every 5 seconds
}

module.exports = { startHeartbeat };
