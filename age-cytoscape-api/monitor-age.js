const { Pool } = require('pg');

const pool = new Pool({
  user: 'sam',
  host: 'localhost',
  database: 'postgres',
  password: '124141',
  port: 5432,
});

async function monitorAGE() {
  const client = await pool.connect();
  
  try {
    // Ensure AGE is loaded
    await client.query("LOAD 'age'");
    await client.query("SET search_path = ag_catalog, '$user', public");
    
    console.log('=== AGE Database Monitor ===\n');
    
    // 1. List all graphs
    const graphsResult = await client.query('SELECT * FROM ag_graph ORDER BY name');
    console.log(`📊 Total Graphs: ${graphsResult.rows.length}\n`);
    
    if (graphsResult.rows.length === 0) {
      console.log('No AGE graphs found.\n');
      return;
    }
    
    // 2. For each graph, show details
    for (const graph of graphsResult.rows) {
      console.log(`🔹 Graph: "${graph.name}"`);
      console.log(`   ID: ${graph.graphid}`);
      console.log(`   Namespace: ${graph.namespace}`);
      
      try {
        // Count nodes
        const nodeCountQuery = `
          SELECT COUNT(*) as count FROM cypher('${graph.name}', $$
            MATCH (n) RETURN n
          $$) AS (node agtype)
        `;
        const nodeCount = await client.query(nodeCountQuery);
        
        // Count edges  
        const edgeCountQuery = `
          SELECT COUNT(*) as count FROM cypher('${graph.name}', $$
            MATCH ()-[r]->() RETURN r
          $$) AS (edge agtype)
        `;
        const edgeCount = await client.query(edgeCountQuery);
        
        console.log(`   Nodes: ${nodeCount.rows[0].count}`);
        console.log(`   Edges: ${edgeCount.rows[0].count}`);
        
        // Show node labels if any nodes exist
        if (parseInt(nodeCount.rows[0].count) > 0) {
          try {
            const labelsQuery = `
              SELECT node FROM cypher('${graph.name}', $$
                MATCH (n) RETURN n
              $$) AS (node agtype)
              LIMIT 5
            `;
            const labels = await client.query(labelsQuery);
            
            if (labels.rows.length > 0) {
              const labelSet = new Set();
              labels.rows.forEach(row => {
                try {
                  // Strip AGE type suffix and parse JSON
                  const nodeStr = row.node.replace(/::vertex$/, '');
                  const nodeData = JSON.parse(nodeStr);
                  if (nodeData.label) {
                    labelSet.add(nodeData.label);
                  }
                } catch (e) {
                  // Skip unparseable nodes
                }
              });
              
              if (labelSet.size > 0) {
                console.log(`   Node Types: ${Array.from(labelSet).join(', ')}`);
              }
            }
          } catch (error) {
            console.log(`   Node Types: Unable to determine (${error.message})`);
          }
        }
        
      } catch (error) {
        console.log(`   Error querying graph: ${error.message}`);
      }
      
      console.log('');
    }
    
    // 3. Show AGE system info
    console.log('=== AGE System Info ===');
    
    // Check AGE extension
    const extResult = await client.query(
      "SELECT * FROM pg_extension WHERE extname = 'age'"
    );
    
    if (extResult.rows.length > 0) {
      console.log(`✅ AGE Extension: v${extResult.rows[0].extversion}`);
    } else {
      console.log('❌ AGE Extension: Not installed');
    }
    
    // Check search path
    const searchPathResult = await client.query('SHOW search_path');
    console.log(`🔍 Search Path: ${searchPathResult.rows[0].search_path}`);
    
  } catch (error) {
    console.error('Error monitoring AGE:', error.message);
  } finally {
    client.release();
    pool.end();
  }
}

// Run if called directly
if (require.main === module) {
  monitorAGE().catch(console.error);
}

module.exports = { monitorAGE };