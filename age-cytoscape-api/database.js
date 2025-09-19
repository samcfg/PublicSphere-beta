const { Pool } = require('pg');
const pool = new Pool({
  user: 'sam',
  host: 'localhost',
  database: 'postgres',
  password: '124141',
  port: 5432,
});

// Set AGE environment on connection
pool.on('connect', async (client) => {
  try {
    await client.query("LOAD 'age'");
    await client.query("SET search_path = ag_catalog, '$user', public");
  } catch (error) {
    console.error('Error setting up AGE environment:', error);
  }
});

async function getGraphData() {
  const client = await pool.connect();
  
  try {
    // Ensure AGE is loaded for this specific client
    await client.query("LOAD 'age'");
    await client.query("SET search_path = ag_catalog, '$user', public");
    
    // Check if graph exists, create if it doesn't
    const graphCheck = await client.query("SELECT * FROM ag_graph WHERE name = 'test_graph'");
    if (graphCheck.rows.length === 0) {
      await client.query("SELECT create_graph('test_graph')");
    }
    
    // Query all nodes from test_graph
    const nodeQuery = `
      SELECT * FROM cypher('test_graph', $$
        MATCH (n)
        RETURN n
      $$) AS (node agtype)
    `;
    
    // Query all edges from test_graph  
    const edgeQuery = `
      SELECT * FROM cypher('test_graph', $$
        MATCH (a)-[r]->(b)
        RETURN a, r, b
      $$) AS (source agtype, edge agtype, target agtype)
    `;
    
    const nodeResult = await client.query(nodeQuery);
    const edgeResult = await client.query(edgeQuery);
    
    return formatForCytoscape(nodeResult.rows, edgeResult.rows);
    
  } finally {
    client.release();
  }
}

function formatForCytoscape(nodes, edges) {
  const elements = [];
  
  // Process nodes
  nodes.forEach((row, index) => {
    try {
      // AGE returns data with type suffixes like ::vertex, ::edge - strip them
      const nodeDataString = row.node.replace(/::vertex$/, '').replace(/::edge$/, '');
      const nodeData = JSON.parse(nodeDataString);
      elements.push({
        data: {
          id: nodeData.properties.id || nodeData.id.toString(),
          label: nodeData.label || 'Unknown',
          ...nodeData.properties
        }
      });
    } catch (error) {
      console.error(`Failed to parse node:`, error.message);
    }
  });
  
  // Process edges
  edges.forEach(row => {
    try {
      // AGE returns data with type suffixes - strip them before parsing
      const sourceString = row.source.replace(/::vertex$/, '').replace(/::edge$/, '');
      const edgeString = row.edge.replace(/::vertex$/, '').replace(/::edge$/, '');
      const targetString = row.target.replace(/::vertex$/, '').replace(/::edge$/, '');
      
      const source = JSON.parse(sourceString);
      const edge = JSON.parse(edgeString);
      const target = JSON.parse(targetString);
      
      elements.push({
        data: {
          id: edge.properties.id || edge.id.toString(),
          source: source.properties.id || source.id.toString(),
          target: target.properties.id || target.id.toString(),
          type: edge.label || '',
          ...edge.properties
        }
      });
    } catch (error) {
      console.error('Failed to parse edge:', error.message);
    }
  });
  
  return { elements };
}

module.exports = { getGraphData };