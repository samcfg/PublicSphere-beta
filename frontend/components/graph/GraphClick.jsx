import { PositionedOverlay } from './PositionedOverlay.jsx';

/**
 * Reusable graph element click tooltip
 * Handles entrance animation and positioning for both nodes and edges
 *
 * @param {Object} props
 * @param {Object} props.cytoElement - Cytoscape node or edge element
 * @param {Object} props.cy - Cytoscape instance
 * @param {Object} props.offset - Positioning offset {x, y}
 * @param {Object} props.clickOffset - Click position offset for animation {x, y}
 * @param {ReactNode} props.children - Content to display in tooltip
 * @param {string} props.className - Optional className for custom styling context
 */
export function GraphClick({ cytoElement, cy, offset = { x: 20, y: -10 }, clickOffset = { x: 0, y: 0 }, className, children }) {
  if (!cytoElement || !cy) return null;

  // Calculate halfway point between click and final position for entrance animation
  const startX = clickOffset.x / 2;
  const startY = clickOffset.y / 2;

  return (
    <PositionedOverlay
      cytoElement={cytoElement}
      cy={cy}
      offset={offset}
    >
      <div
        className={`graph-tooltip-container ${className || ''}`}
        style={{
          '--start-x': `${startX}px`,
          '--start-y': `${startY}px`
        }}
      >
        <div className="graph-tooltip-highlight">
          <div className="graph-tooltip">
            <div className="tooltip-content">
              {children}
            </div>
          </div>
        </div>
      </div>
    </PositionedOverlay>
  );
}
