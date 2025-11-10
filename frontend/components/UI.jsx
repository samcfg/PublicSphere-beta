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
 */
export function GraphControls({ onLoadGraph, onResetView, onFitScreen }) {
  return (
    <div className="header">
      <h1>Map of an Argument</h1>
      <div className="controls">
        <button id="load-btn" onClick={onLoadGraph}>
          Load Graph
        </button>
        <button id="reset-btn" onClick={onResetView}>
          Reset View
        </button>
        <button id="fit-btn" onClick={onFitScreen}>
          Fit to Screen
        </button>
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
 */
export function UI({
  onLoadGraph,
  onResetView,
  onFitScreen,
  statusMessage,
  statusType
}) {
  return (
    <>
      <GraphControls
        onLoadGraph={onLoadGraph}
        onResetView={onResetView}
        onFitScreen={onFitScreen}
      />

      <StatusBar message={statusMessage} type={statusType} />

      <EdgeTooltip />
    </>
  );
}
