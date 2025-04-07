const express = require('express');
const app = express();
const PORT = 3000;

const nodeRoutes = require('./routes/nodeRoutes');
const heartbeatRoutes = require('./routes/heartbeatRoutes');

app.use(express.json());
app.use('/node', nodeRoutes);
app.use('/heartbeat', heartbeatRoutes);

app.listen(PORT, () => {
    console.log(`API Server running on http://localhost:${PORT}`);
});
