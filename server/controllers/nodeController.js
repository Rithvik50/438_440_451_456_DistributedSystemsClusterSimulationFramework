const nodeManager = require('../utils/nodeManager');

exports.registerNode = (req, res) => {
  const { cpu } = req.body;
  const node = nodeManager.addNode(cpu);
  res.status(201).json(node);
};

exports.listNodes = (req, res) => {
  const nodes = nodeManager.getAllNodes();
  res.json(nodes);
};

exports.receiveHeartbeat = (req, res) => {
  const { nodeId } = req.body;
  const success = nodeManager.updateHeartbeat(nodeId);
  if (success) {
    res.status(200).json({ message: 'Heartbeat received' });
  } else {
    res.status(404).json({ message: 'Node not found' });
  }
};