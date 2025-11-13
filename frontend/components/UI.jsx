import { useState, useEffect } from 'react';
import '../styles/components/button.css';

/**
 * UI controls and status display component
 * Handles graph control buttons, status messages, and will expand to include
 * authentication UI, user profiles, and social features in Phase 3
 */

/**
 * Control buttons for graph operations
 * @param {Object} props
 * @param {Function} props.onLoadGraph - Callback for loading graph data
 * @param {Function} props.onResetView - Callback for resetting graph view
 * @param {Function} props.onFitScreen - Callback for fitting graph to screen
 * @param {Object} props.graphStats - Graph statistics {nodeCount, edgeCount}
 */
export function GraphControls({ onLoadGraph, onResetView, onFitScreen, graphStats }) {
  const [dyslexiaMode, setDyslexiaMode] = useState(false);

  // Load preference from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('dyslexiaMode');
    if (saved === 'true') {
      setDyslexiaMode(true);
      document.documentElement.classList.add('dyslexia-mode');
    }
  }, []);

  const toggleDyslexiaMode = () => {
    const newMode = !dyslexiaMode;
    setDyslexiaMode(newMode);

    if (newMode) {
      document.documentElement.classList.add('dyslexia-mode');
    } else {
      document.documentElement.classList.remove('dyslexia-mode');
    }

    localStorage.setItem('dyslexiaMode', newMode.toString());
  };

  return (
    <div className="header">
      <div className="title-section">
        <h1>Map of an Argument</h1>
        {graphStats && (
          <>
            <div className="graph-stats">
              {graphStats.nodeCount} nodes · {graphStats.edgeCount} connections
            </div>
            <hr className="title-divider" />
          </>
        )}
      </div>
      <div className="controls">
        <div className="box">
          <button id="reset-btn" onClick={onResetView}>
            Reset View
          </button>
        </div>
        <div className="box">
          <button id="fit-btn" onClick={onFitScreen}>
            Fit to Screen
          </button>
        </div>
        <div className="box">
          <button id="dyslexia-btn" onClick={toggleDyslexiaMode}>
            {dyslexiaMode ? 'Serif Font' : 'Dyslexia Font'}
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * Status bar for displaying messages
 * @param {Object} props
 * @param {string} props.message - Status message to display
 * @param {string} props.type - Message type: 'info' | 'success' | 'error' | 'loading'
 */
export function StatusBar({ message, type = 'info' }) {
  // Map type to CSS class
  const className = type === 'success' ? 'success' : type === 'error' ? 'error' : '';

  return (
    <div id="status" className={className}>
      {message}
    </div>
  );
}

/**
 * Edge tooltip (positioned absolutely by Graph component)
 * This component just provides the DOM structure - Graph.jsx handles positioning
 */
export function EdgeTooltip() {
  return (
    <div id="edge-tooltip">
      <div className="tooltip-label">Edge Notes:</div>
      <div className="tooltip-content"></div>
    </div>
  );
}

/**
 * Main UI component combining all UI elements
 * @param {Object} props
 * @param {Function} props.onLoadGraph - Callback for loading graph data
 * @param {Function} props.onResetView - Callback for resetting graph view
 * @param {Function} props.onFitScreen - Callback for fitting graph to screen
 * @param {string} props.statusMessage - Current status message
 * @param {string} props.statusType - Status message type
 * @param {Object} props.graphStats - Graph statistics {nodeCount, edgeCount}
 */
export function UI({
  onLoadGraph,
  onResetView,
  onFitScreen,
  statusMessage,
  statusType,
  graphStats
}) {
  return (
    <>
      <GraphControls
        onLoadGraph={onLoadGraph}
        onResetView={onResetView}
        onFitScreen={onFitScreen}
        graphStats={graphStats}
      />

      <StatusBar message={statusMessage} type={statusType} />

      <EdgeTooltip />
    </>
  );
}
