# AGE-Cytoscape API

API server that visualizes Apache AGE graph databases using Cytoscape.js

## Prerequisites

1. PostgreSQL with AGE extension installed
2. Node.js and npm/pnpm
3. AGE database with graph data

## Setup Procedure

### 1. Install Dependencies
```bash
cd /.../PS_SE_backend_Aug29/age-cytoscape-api
npm install
# or
pnpm install
```

### 2. Configure Database Connection
Edit `database.js` if needed to match your PostgreSQL setup:
```javascript
const pool = new Pool({
  user: 'sam',
  host: 'localhost', 
  database: 'postgres',
  password: '124141',
  port: 5432,
});
```

### 3. Start the Server
```bash
node server.js
```

You should see:
```
Server running on port 3001
Graph endpoint: http://localhost:3001/graph
```

### 4. View the Graph Visualization
Open your web browser and navigate to:
```
http://localhost:3001/index.html
```

## API Endpoints

- `GET /health` - Health check
- `GET /graph` - Returns graph data in Cytoscape format
- `GET /index.html` - Graph visualization interface

## Graph Configuration

The API currently visualizes the graph named `test_graph`. To change this:

1. Edit the graph name in `database.js`:
```javascript
// Change 'test_graph' to your graph name
const graphCheck = await client.query("SELECT * FROM ag_graph WHERE name = 'your_graph_name'");
```

2. Update the queries:
```javascript
const nodeQuery = `
  SELECT * FROM cypher('your_graph_name', $$
    MATCH (n)
    RETURN n
  $$) AS (node agtype)
`;
```

## Monitoring AGE Databases

To view all your AGE graphs and their statistics:
```bash
node monitor-age.js
```

This shows:
- List of all AGE graphs
- Node and edge counts per graph
- Node types/labels
- AGE extension version
- System configuration

## Troubleshooting

### Server won't start
- Check PostgreSQL is running
- Verify AGE extension is installed
- Check database credentials

### No graph data
- Verify your AGE graph contains data
- Check graph name matches in queries
- Check browser console for errors
- Use `node monitor-age.js` to see available graphs

## Data Format

The API converts AGE data format:
```
{"id": 123, "label": "Person", "properties": {"name": "John"}}::vertex
```

To Cytoscape format:
```json
{
  "data": {
    "id": "123",
    "label": "John", 
    "name": "John"
  }
}
```