const { v4: uuidv4 } = require('uuid');

const nodes = new Map();

exports.addNode = (cpu) => {
  const id = uuidv4();
  const node = {
    id,
    cpu,
    pods: [],
    lastHeartbeat: new Date(),
    status: 'Healthy',
  };
  nodes.set(id, node);
  return node;
};

exports.getAllNodes = () => Array.from(nodes.values());

exports.updateHeartbeat = (nodeId) => {
  const node = nodes.get(nodeId);
  if (!node) return false;
  node.lastHeartbeat = new Date();
  node.status = 'Healthy';
  return true;
};