import { useRef, useState, useEffect } from 'react';
import { useGraphData } from '../hooks/useGraphData.js';
import { formatForCytoscape } from '../utilities/formatters.js';
import { Graph } from './Graph.jsx';
import { UI } from './UI.jsx';

/**
 * Graph page component
 * Orchestrates data flow between API, formatting, and visualization
 */
export function GraphPage() {
  const { data, loading, error, refetch } = useGraphData();
  const graphRef = useRef(null); // Reference to Graph component for imperative methods
  const [statusMessage, setStatusMessage] = useState('');
  const [statusType, setStatusType] = useState('info');
  const [formattedData, setFormattedData] = useState(null);
  const [graphStats, setGraphStats] = useState(null);

  // Update status message and graph stats based on loading/error state
  useEffect(() => {
    if (loading) {
      setStatusMessage('Loading graph data...');
      setStatusType('loading');
      setGraphStats(null);
    } else if (error) {
      setStatusMessage(`Error: ${error}`);
      setStatusType('error');
      setGraphStats(null);
    } else if (data) {
      // Calculate stats for status display
      const elements = formattedData?.elements || [];
      const nodes = elements.filter(el => !el.data.source && !el.data.target);
      const edges = elements.filter(el => el.data.source && el.data.target);

      setGraphStats({
        nodeCount: nodes.length,
        edgeCount: edges.length
      });

      setStatusMessage(
        `Loaded ${elements.length} elements (${nodes.length} nodes, ${edges.length} edges)`
      );
      setStatusType('success');
    }
  }, [loading, error, data, formattedData]);

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
      setStatusMessage(`Formatting error: ${err.message}`);
      setStatusType('error');
    }
  }, [data]);

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
    <>
      <UI
        onLoadGraph={handleLoadGraph}
        onResetView={handleResetView}
        onFitScreen={handleFitScreen}
        statusMessage={statusMessage}
        statusType={statusType}
        graphStats={graphStats}
      />

      <Graph ref={graphRef} data={formattedData} />
    </>
  );
}
