const express = require('express');
const router = express.Router();
const nodeController = require('../controllers/nodeController');

router.post('/', nodeController.registerNode);
router.get('/', nodeController.listNodes);

module.exports = router;
