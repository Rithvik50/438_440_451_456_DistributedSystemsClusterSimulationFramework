const axios = require('axios');
const { startHeartbeat } = require('./heartbeat');

const API_SERVER = 'http://host.docker.internal:3000'; 
const CPU = 2;

(async () => {
  try {
    const res = await axios.post(`${API_SERVER}/nodes`, { cpu: CPU });
    const nodeId = res.data.id;
    console.log(`Registered node with ID: ${nodeId}`);
    startHeartbeat(nodeId);
  } catch (err) {
    console.error('Failed to register node:', err.message);
  }
})();
