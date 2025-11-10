/**
 * Transform DRF API graph response into Cytoscape.js format
 * Backend already parses AGE format - this transforms the clean JSON structure
 * @param {Object} graphData - {claims: [...], sources: [...], edges: [...]} from /api/graph/
 * @returns {Object} - {elements: [...]} formatted for Cytoscape
 */
export function formatForCytoscape(graphData) {
  const elements = [];

  // Process claims (nodes)
  if (graphData.claims) {
    graphData.claims.forEach((row) => {
      try {
        const claim = row.claim; // Already parsed by database.py
        elements.push({
          data: {
            id: claim.properties.id,
            label: claim.label || 'Claim',
            type: 'claim',
            ...claim.properties
          },
          classes: 'claim' // CSS class for styling
        });
      } catch (error) {
        console.error('Failed to process claim:', error.message, row);
      }
    });
  }

  // Process sources (nodes)
  if (graphData.sources) {
    graphData.sources.forEach((row) => {
      try {
        const source = row.source; // Already parsed by database.py
        elements.push({
          data: {
            id: source.properties.id,
            label: source.label || 'Source',
            type: 'source',
            ...source.properties
          },
          classes: 'source' // CSS class for styling
        });
      } catch (error) {
        console.error('Failed to process source:', error.message, row);
      }
    });
  }

  // Process edges (connections)
  if (graphData.edges) {
    graphData.edges.forEach((row) => {
      try {
        const connection = row.connection; // Already parsed by database.py

        // AGE edges have start_id (source) and end_id (target) - use these for correct direction
        // Compare AGE internal IDs to determine which node is source vs target
        const sourceNode = row.node.id === connection.start_id ? row.node : row.other;
        const targetNode = row.node.id === connection.end_id ? row.node : row.other;

        elements.push({
          data: {
            id: connection.properties.id,
            source: sourceNode.properties.id,  // Correct source based on start_id
            target: targetNode.properties.id,  // Correct target based on end_id
            label: connection.label || 'Connection',
            composite_id: connection.properties.composite_id,
            logic_type: connection.properties.logic_type,
            notes: connection.properties.notes,
            ...connection.properties
          },
          classes: connection.properties.logic_type || 'connection' // CSS class based on logic type
        });
      } catch (error) {
        console.error('Failed to process edge:', error.message, row);
      }
    });
  }

  return { elements };
}
