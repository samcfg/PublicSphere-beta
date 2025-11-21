import { useRef, useState, useEffect } from 'react';
import { useGraphData } from '../hooks/useGraphData.js';
import { formatForCytoscape } from '../utilities/formatters.js';
import { Graph } from '../components/graph/Graph.jsx';
import { GraphControls } from '../components/graph/GraphControls.jsx';
import { AttributionProvider } from '../utilities/AttributionContext.jsx';

/**
 * Graph page component
 * Orchestrates data flow between API, formatting, and visualization
 */
export function GraphPage() {
  const { data, attributions: initialAttributions, loading, error, refetch } = useGraphData();
  const graphRef = useRef(null); // Reference to Graph component for imperative methods
  const [formattedData, setFormattedData] = useState(null);
  const [graphStats, setGraphStats] = useState(null);
  const [attributions, setAttributions] = useState({});

  // Sync attributions from hook
  useEffect(() => {
    setAttributions(initialAttributions);
  }, [initialAttributions]);

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

  // Format data when raw API response changes
  useEffect(() => {
    if (!data) {
      setFormattedData(null);
      return;
    }

    try {
      const formatted = formatForCytoscape(data);
      setFormattedData(formatted);
    } catch (err) {
      console.error('Error formatting graph data:', err);
    }
  }, [data]);

  // Attribution cache updater for local graph manipulation
  const updateAttributions = (modifications) => {
    setAttributions(prev => {
      const next = {...prev};
      if (modifications.add) {
        Object.assign(next, modifications.add);
      }
      if (modifications.remove) {
        modifications.remove.forEach(uuid => delete next[uuid]);
      }
      return next;
    });
  };

  // Control handlers
  const handleLoadGraph = () => {
    refetch(); // Trigger data refresh
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

      <Graph
        ref={graphRef}
        data={formattedData}
        updateAttributions={updateAttributions}
        onGraphChange={refetch}
      />
    </AttributionProvider>
  );
}
