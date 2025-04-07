// === server/routes/heartbeatRoutes.js ===
const express = require('express');
const router = express.Router();
const nodeController = require('../controllers/nodeController');

router.post('/', nodeController.receiveHeartbeat);

module.exports = router;