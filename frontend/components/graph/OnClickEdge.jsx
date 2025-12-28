import { useNavigate } from 'react-router-dom';
import { PositionedOverlay } from './PositionedOverlay.jsx';
import { UserAttribution } from '../common/UserAttribution.jsx';
import { CommentsRating } from '../common/CommentsRating.jsx';
import { FaMagnifyingGlassArrowRight } from "react-icons/fa6";

/**
 * Edge tooltip component that displays edge data on click
 * Shows attribution, logic type, and notes
 *
 * @param {Object} props
 * @param {Object} props.activeEdgeTooltip - {edge: cytoscapeEdge, clickOffset: {x, y}} or null
 * @param {Object} props.cy - Cytoscape instance
 */
export function OnClickEdge({ activeEdgeTooltip, cy }) {
  const navigate = useNavigate();

  if (!activeEdgeTooltip || !cy) return null;

  const edge = activeEdgeTooltip.edge;
  const edgeId = edge.data('id');
  const logicType = edge.data('logic_type');
  const notes = edge.data('notes');
  const clickOffset = activeEdgeTooltip.clickOffset || { x: 0, y: 0 };

  // Calculate animation start position
  const startX = clickOffset.x / 2;
  const startY = clickOffset.y / 2;

  // Determine highlight color based on logic type
  const getEdgeColor = () => {
    const rootStyles = getComputedStyle(document.documentElement);
    if (logicType === 'NOT' || logicType === 'NAND') {
      return '#e74c3c'; // Red for negative logic
    }
    return rootStyles.getPropertyValue('--accent-green').trim(); // Green for positive logic
  };

  const highlightColor = getEdgeColor();

  return (
    <PositionedOverlay
      cytoElement={edge}
      cy={cy}
      offset={{ x: 20, y: -10 }}
    >
      <div
        className="graph-tooltip-container"
        style={{
          '--start-x': `${startX}px`,
          '--start-y': `${startY}px`
        }}
      >
        <div className="graph-tooltip-highlight" style={{ backgroundColor: highlightColor }}>
          <div className="graph-tooltip" onClick={(e) => e.stopPropagation()} style={{ display: 'flex', flexDirection: 'column', boxShadow: 'none', maxWidth: '300px', minWidth: 'unset' }}>
            <div className="tooltip-content" style={{ flex: '1 1 auto' }}>
              <div className="tooltip-attribution" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <UserAttribution entityUuid={edgeId} entityType="connection" showTimestamp={true} />
                <FaMagnifyingGlassArrowRight
                  onClick={() => navigate(`/connectionview?id=${edgeId}`)}
                  style={{ cursor: 'pointer', fontSize: '16px' }}
                  title="Expand view"
                />
              </div>
              {logicType && (
                <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid var(--border-color)' }}>
                  <div style={{ fontSize: '9px', color: 'var(--text-muted)', marginBottom: '2px' }}>
                    Logic
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: '1.4', overflowWrap: 'break-word' }}>
                    {logicType}
                  </div>
                </div>
              )}
              {notes && (
                <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid var(--border-color)' }}>
                  <div style={{ fontSize: '9px', color: 'var(--text-muted)', marginBottom: '2px' }}>
                    Notes
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: '1.4', overflowWrap: 'break-word' }}>
                    {notes}
                  </div>
                </div>
              )}
            </div>
            <div className="tooltip-comments-rating" style={{
              marginTop: 'auto',
              marginLeft: '-8px',
              marginRight: '-8px',
              marginBottom: '-8px'
            }}>
              <CommentsRating entityUuid={edgeId} entityType="connection" entityColor={highlightColor} />
            </div>
          </div>
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

    // Capture rendered click position relative to the container position
    // The container will be positioned at edge.renderedMidpoint() + offset
    const renderedClick = event.renderedPosition;
    const edgeMidpoint = edge.renderedMidpoint();
    const containerOffset = { x: 20, y: -10 }; // Must match GraphClick offset

    const clickOffset = {
      x: renderedClick.x - (edgeMidpoint.x + containerOffset.x),
      y: renderedClick.y - (edgeMidpoint.y + containerOffset.y)
    };

    setActiveEdgeTooltip({ edge, clickOffset });

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
