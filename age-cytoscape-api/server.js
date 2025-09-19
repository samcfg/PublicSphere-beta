const express = require('express');
const cors = require('cors');
const path = require('path');
const { getGraphData } = require('./database');

const app = express();
const PORT = 3001;

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname)));

app.get('/graph', async (req, res) => {
  try {
    const graphData = await getGraphData();
    res.json(graphData);
  } catch (error) {
    console.error('Error fetching graph data:', error);
    res.status(500).json({ error: 'Failed to fetch graph data' });
  }
});

app.get('/health', (req, res) => {
  res.json({ status: 'ok', message: 'AGE-Cytoscape API running' });
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  console.log(`Graph endpoint: http://localhost:${PORT}/graph`);
});