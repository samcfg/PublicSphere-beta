import { useState, useEffect } from 'react';
import '../../styles/components/button.css';
// Contains title and buttons

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
