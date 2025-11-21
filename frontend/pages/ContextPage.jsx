import { useRef, useState, useEffect } from 'react';
import { useGraphData } from '../hooks/useGraphData.js';
import { formatForCytoscape } from '../utilities/formatters.js';
import { Graph } from '../components/graph/Graph.jsx';
import { GraphControls } from '../components/graph/GraphControls.jsx';
import { AttributionProvider } from '../utilities/AttributionContext.jsx';

// Hardcoded for now - will be dynamic later
const TARGET_NODE_ID = 'ff68b489-3fa0-4d41-84a1-f085b92bf6f7';

/**
 * Compute all predecessor node IDs (nodes on incoming paths to target)
 * @param {Array} elements - Cytoscape elements array
 * @param {string} targetId - Target node ID
 * @returns {Set} Set of node IDs that are predecessors (including target)
 */
function computePredecessors(elements, targetId) {
  // Build adjacency list (reverse direction: target -> sources)
  const incomingEdges = new Map(); // nodeId -> [sourceNodeIds]

  elements.forEach(el => {
    if (el.data.source && el.data.target) {
      // This is an edge
      const target = el.data.target;
      const source = el.data.source;

      if (!incomingEdges.has(target)) {
        incomingEdges.set(target, []);
      }
      incomingEdges.get(target).push(source);
    }
  });

  // BFS from target node backwards
  const predecessors = new Set([targetId]);
  const queue = [targetId];

  while (queue.length > 0) {
    const current = queue.shift();
    const sources = incomingEdges.get(current) || [];

    for (const sourceId of sources) {
      if (!predecessors.has(sourceId)) {
        predecessors.add(sourceId);
        queue.push(sourceId);
      }
    }
  }

  return predecessors;
}

/**
 * Filter elements to only include predecessors of target node
 * @param {Object} data - Formatted Cytoscape data {elements: [...]}
 * @param {string} targetId - Target node ID
 * @returns {Object} Filtered data with only predecessor elements
 */
function filterToContext(data, targetId) {
  if (!data?.elements) return data;

  const predecessorIds = computePredecessors(data.elements, targetId);

  const filteredElements = data.elements.filter(el => {
    if (el.data.source && el.data.target) {
      // Edge: include if both endpoints are in predecessor set
      return predecessorIds.has(el.data.source) && predecessorIds.has(el.data.target);
    } else {
      // Node: include if in predecessor set
      return predecessorIds.has(el.data.id);
    }
  });

  return { elements: filteredElements };
}

/**
 * Context page component - displays argument context for a specific conclusion node
 * Shows all premise nodes and connections leading to the target node
 */
export function ContextPage() {
  const { data, attributions, loading, error, refetch } = useGraphData();
  const graphRef = useRef(null);
  const [formattedData, setFormattedData] = useState(null);
  const [graphStats, setGraphStats] = useState(null);

  // Calculate graph stats when data changes
  useEffect(() => {
    if (data && formattedData) {
      const elements = formattedData.elements || [];
      const nodes = elements.filter(el => !el.data.source && !el.data.target);
      const edges = elements.filter(el => el.data.source && el.data.target);

      setGraphStats({
        nodeCount: nodes.length,
        edgeCount: edges.length
      });
    } else {
      setGraphStats(null);
    }
  }, [data, formattedData]);

  // Format and filter data when raw API response changes
  useEffect(() => {
    if (!data) {
      setFormattedData(null);
      return;
    }

    try {
      const formatted = formatForCytoscape(data);
      const contextData = filterToContext(formatted, TARGET_NODE_ID);
      setFormattedData(contextData);
    } catch (err) {
      console.error('Error formatting context data:', err);
    }
  }, [data]);

  // Control handlers
  const handleLoadGraph = () => {
    refetch();
  };

  const handleResetView = () => {
    if (graphRef.current) {
      graphRef.current.resetView();
    }
  };

  const handleFitScreen = () => {
    if (graphRef.current) {
      graphRef.current.fitToScreen();
    }
  };

  return (
    <AttributionProvider attributions={attributions}>
      <GraphControls
        onLoadGraph={handleLoadGraph}
        onResetView={handleResetView}
        onFitScreen={handleFitScreen}
        graphStats={graphStats}
      />

      <Graph ref={graphRef} data={formattedData} />
    </AttributionProvider>
  );
}
