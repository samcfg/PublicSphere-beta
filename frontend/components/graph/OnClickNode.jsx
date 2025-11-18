import { PositionedOverlay } from './PositionedOverlay.jsx';
import { UserAttribution } from '../common/UserAttribution.jsx';
import { CommentsRating } from '../common/CommentsRating.jsx';

/**
 * Node frame component that displays node data on click
 * Shows attribution, comments, and ratings in L-shaped frame
 *
 * @param {Object} props
 * @param {Object} props.activeNodeTooltip - {node: cytoscapeNode, clickOffset: {x, y}} or null
 * @param {Object} props.cy - Cytoscape instance
 */
export function OnClickNode({ activeNodeTooltip, cy }) {
  if (!activeNodeTooltip || !cy) return null;

  const node = activeNodeTooltip.node;
  const nodeId = node.data('id');
  const nodeType = node.data('type'); // 'claim' or 'source'
  const nodeLabel = node.data('label');
  const nodeUrl = node.data('url'); // Only present on source nodes
  const clickOffset = activeNodeTooltip.clickOffset || { x: 0, y: 0 };

  // Determine entity type for attribution/comments
  const entityType = nodeType === 'source' ? 'source' : 'claim';

  // Get node dimensions in graph coordinates (use outerWidth/outerHeight for visual edges)
  const nodeOuterWidth = node.outerWidth();
  const nodeOuterHeight = node.outerHeight();

  // Get zoom to convert pixel values to graph coordinates
  const zoom = cy.zoom();

  // Debug: Check values
  console.log('Node ID:', nodeId);
  console.log('node.outerWidth():', nodeOuterWidth);
  console.log('node.outerHeight():', nodeOuterHeight);
  console.log('zoom:', zoom);

  // Node edge positions relative to node center (outerWidth/Height already includes padding/border)
  const nodeEdges = {
    left: -(nodeOuterWidth / 2),
    right: (nodeOuterWidth / 2),
    top: -(nodeOuterHeight / 2),
    bottom: (nodeOuterHeight / 2)
  };

  // Frame dimensions in graph coordinates (convert from desired pixel sizes)
  const frameRightWidth = 150 / zoom;
  const frameBottomHeight = 80;

  // Frame right edges (top-left at node's top-right)
  const frameRightEdges = {
    left: nodeEdges.right,
    right: nodeEdges.right + frameRightWidth,
    top: nodeEdges.top,
    bottom: nodeEdges.bottom
  };

  // Frame bottom edges (top-left at node's bottom-left)
  const bottomFrameWidth = (frameRightEdges.right - nodeEdges.left) * 0.93; // 7% reduction
  const frameBottomEdges = {
    left: nodeEdges.left,
    right: nodeEdges.left + bottomFrameWidth,
    top: nodeEdges.bottom,
    bottom: nodeEdges.bottom + frameBottomHeight
  };

  // Debug: Check calculated frame dimensions
  console.log('Right frame - width:', frameRightEdges.right - frameRightEdges.left);
  console.log('Right frame - height:', frameRightEdges.bottom - frameRightEdges.top);
  console.log('Bottom frame - width:', frameBottomEdges.right - frameBottomEdges.left);
  console.log('Bottom frame - height:', frameBottomEdges.bottom - frameBottomEdges.top);

  // Animation start positions
  const startX = clickOffset.x / 2;
  const startY = clickOffset.y / 2;

  return (
    <>
      {/* Frame with node cutout */}
      <PositionedOverlay
        cytoElement={node}
        cy={cy}
        offset={{ x: nodeEdges.left - 20, y: nodeEdges.top - 20 }}
        passThrough={true}
      >
        {(() => {
          // Frame padding around node
          const padding = 20;
          const bottomExtension = 100; // Extra space below node for content
          const borderRadius = 8;
          // Total frame dimensions
          const frameWidth = nodeOuterWidth + padding * 2;
          const frameHeight = nodeOuterHeight + padding * 2 + bottomExtension;
          // Cutout position (relative to frame top-left)
          const cutoutLeft = padding;
          const cutoutTop = padding;
          const cutoutRight = padding + nodeOuterWidth;
          const cutoutBottom = padding + nodeOuterHeight;

          // Clip path: outer rectangle clockwise, then inner rectangle counter-clockwise
          const clipPath = `polygon(
            0% 0%, 100% 0%, 100% 100%, 0% 100%, 0% 0%,
            ${cutoutLeft}px ${cutoutTop}px,
            ${cutoutLeft}px ${cutoutBottom}px,
            ${cutoutRight}px ${cutoutBottom}px,
            ${cutoutRight}px ${cutoutTop}px,
            ${cutoutLeft}px ${cutoutTop}px
          )`;

          return (
            <div style={{
              width: `${frameWidth}px`,
              height: `${frameHeight}px`,
              backgroundColor: 'var(--node-default)',
              clipPath: clipPath,
              borderRadius: `${borderRadius}px`,
              position: 'relative',
              pointerEvents: 'none'
            }}>
              {/* Content area below the node cutout */}
              <div style={{
                position: 'absolute',
                top: `${cutoutBottom + 10}px`,
                left: `${padding}px`,
                right: `${padding}px`,
                bottom: `${padding}px`,
                color: 'var(--node-text)',
                fontSize: '12px',
                pointerEvents: 'auto'
              }}>
                <div className="tooltip-content">
                  <div className="tooltip-attribution">
                    <UserAttribution entityUuid={nodeId} entityType={entityType} showTimestamp={true} />
                  </div>
                  {nodeType === 'source' && nodeUrl && (
                    <div><strong>URL:</strong> <a href={nodeUrl} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent-blue)' }}>{nodeUrl}</a></div>
                  )}
                  <div className="tooltip-comments-rating">
                    <CommentsRating entityUuid={nodeId} entityType={entityType} />
                  </div>
                </div>
              </div>
            </div>
          );
        })()}
      </PositionedOverlay>

      {/* Right frame piece - commented out
      <PositionedOverlay
        cytoElement={node}
        cy={cy}
        offset={{ x: frameRightEdges.left, y: frameRightEdges.top }}
      >
        <div
          className="graph-tooltip-container node-frame-right"
          style={{
            '--start-x': `${startX}px`,
            '--start-y': `${startY}px`
          }}
        >
          <div className="graph-tooltip-highlight">
            <div
              className="graph-tooltip"
              style={{
                width: `${frameRightEdges.right - frameRightEdges.left}px`,
                height: `${frameRightEdges.bottom - frameRightEdges.top}px`
              }}
            >
              <div className="tooltip-content">
              </div>
            </div>
          </div>
        </div>
      </PositionedOverlay>
      */}

      {/* Bottom frame piece - commented out
      <PositionedOverlay
        cytoElement={node}
        cy={cy}
        offset={{ x: frameBottomEdges.left, y: frameBottomEdges.top }}
      >
        <div
          className="graph-tooltip-container node-frame-bottom"
          style={{
            '--start-x': `${startX}px`,
            '--start-y': `${startY}px`
          }}
        >
            <div
              className="graph-tooltip"
              style={{
                width: `${nodeOuterWidth}px`,
                height: `${frameBottomEdges.bottom - frameBottomEdges.top}px`,
                border: 'none',
                boxShadow: 'none'
              }}
            >
              <div className="tooltip-content">
              </div>
            </div>
        </div>
      </PositionedOverlay>
      */}
    </>
  );
}

/**
 * Setup event handlers for node tooltip
 * Attaches click handlers to nodes and background for showing/hiding tooltip
 *
 * @param {Object} cy - Cytoscape instance
 * @param {Function} setActiveNodeTooltip - State setter for active tooltip
 * @returns {Function} Cleanup function to remove event listeners
 */
export function setupNodeTooltip(cy, setActiveNodeTooltip) {
  // Click on node to show tooltip
  cy.on('tap', 'node', (event) => {
    const node = event.target;

    // Capture rendered click position relative to the container position
    const renderedClick = event.renderedPosition;
    const nodePosition = node.renderedPosition();
    const containerOffset = { x: 20, y: -10 }; // Must match GraphClick offset

    const clickOffset = {
      x: renderedClick.x - (nodePosition.x + containerOffset.x),
      y: renderedClick.y - (nodePosition.y + containerOffset.y)
    };

    setActiveNodeTooltip({ node, clickOffset });

    event.stopPropagation();
    event.preventDefault();
  });

  // Click on cytoscape background to hide tooltip
  cy.on('tap', (event) => {
    if (event.target === cy) {
      setActiveNodeTooltip(null);
    }
  });

  // Click outside graph to hide tooltip
  const hideTooltip = (event) => {
    const container = cy.container();
    if (!container.contains(event.target)) {
      setActiveNodeTooltip(null);
    }
  };

  document.addEventListener('click', hideTooltip);

  // Return cleanup function
  return () => {
    document.removeEventListener('click', hideTooltip);
  };
}
