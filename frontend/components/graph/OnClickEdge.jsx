import { PositionedOverlay } from './PositionedOverlay.jsx';

/**
 * Edge tooltip component that displays edge notes on click
 * Shows a positioned overlay with edge data when an edge is clicked
 *
 * @param {Object} props
 * @param {Object} props.activeEdgeTooltip - {edge: cytoscapeEdge, notes: string} or null
 * @param {Object} props.cy - Cytoscape instance
 */
export function OnClickEdge({ activeEdgeTooltip, cy }) {
  if (!activeEdgeTooltip || !cy) return null;

  return (
    <PositionedOverlay
      cytoElement={activeEdgeTooltip.edge}
      cy={cy}
      offset={{ x: 20, y: -10 }}
    >
      <div className="edge-tooltip">
        <div className="tooltip-content">
          {activeEdgeTooltip.notes}
        </div>
      </div>
    </PositionedOverlay>
  );
}

/**
 * Setup event handlers for edge tooltip
 * Attaches click handlers to edges and background for showing/hiding tooltip
 *
 * @param {Object} cy - Cytoscape instance
 * @param {Function} setActiveEdgeTooltip - State setter for active tooltip
 * @returns {Function} Cleanup function to remove event listeners
 */
export function setupEdgeTooltip(cy, setActiveEdgeTooltip) {
  // Click on edge to show tooltip
  cy.on('tap', 'edge', (event) => {
    const edge = event.target;
    const notes = edge.data('notes') || 'No notes available';

    setActiveEdgeTooltip({ edge, notes });

    event.stopPropagation();
    event.preventDefault();
  });

  // Click on cytoscape background to hide tooltip
  cy.on('tap', (event) => {
    if (event.target === cy) {
      setActiveEdgeTooltip(null);
    }
  });

  // Click outside graph to hide tooltip
  const hideTooltip = (event) => {
    const container = cy.container();
    if (!container.contains(event.target)) {
      setActiveEdgeTooltip(null);
    }
  };

  document.addEventListener('click', hideTooltip);

  // Return cleanup function
  return () => {
    document.removeEventListener('click', hideTooltip);
  };
}
