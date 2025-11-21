import { useState, useRef, useEffect, useLayoutEffect } from 'react';
import { PositionedOverlay } from './PositionedOverlay.jsx';
import { UserAttribution } from '../common/UserAttribution.jsx';
import { CommentsRating } from '../common/CommentsRating.jsx';
import { NodeCreationModal } from './NodeCreationModal.jsx';
import { useAuth } from '../../utilities/AuthContext.jsx';
import { useAttributions } from '../../utilities/AttributionContext.jsx';
import { deleteClaim, deleteSource } from '../../APInterface/api.js';

/**
 * Node frame component that displays node data on click
 * Shows attribution, comments, and ratings in L-shaped frame
 *
 * @param {Object} props
 * @param {Object} props.activeNodeTooltip - {node: cytoscapeNode, clickOffset: {x, y}} or null
 * @param {Object} props.cy - Cytoscape instance
 * @param {Function} props.updateAttributions - Function to update attribution cache locally
 * @param {Function} props.onGraphChange - Fallback callback for complex graph changes (full refetch)
 * @param {Function} props.onClose - Callback to close the tooltip
 */
export function OnClickNode({ activeNodeTooltip, cy, updateAttributions, onGraphChange, onClose }) {
  const { user, token } = useAuth();
  const attributionsCache = useAttributions();
  const [activeTab, setActiveTab] = useState(null);
  const [contentHeight, setContentHeight] = useState(0);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const contentRef = useRef(null);

  // ResizeObserver to measure content height dynamically
  useEffect(() => {
    if (!contentRef.current) return;

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setContentHeight(entry.contentRect.height);
      }
    });

    observer.observe(contentRef.current);

    return () => observer.disconnect();
  }, [activeNodeTooltip]); // Reconnect when tooltip changes

  // Reset tab when tooltip closes
  useLayoutEffect(() => {
    if (!activeNodeTooltip) {
      setActiveTab(null);
    }
  }, [activeNodeTooltip]);

  // Delete handler
  const handleDelete = async () => {
    if (!token || !activeNodeTooltip) return;
    if (!confirm('Delete this node? This cannot be undone.')) return;

    setIsDeleting(true);
    try {
      const node = activeNodeTooltip.node;
      const nodeId = node.data('id');
      const nodeType = node.data('type');

      const deleteFunc = nodeType === 'source' ? deleteSource : deleteClaim;
      const result = await deleteFunc(token, nodeId);

      if (result.error) {
        alert(`Failed to delete: ${result.error}`);
        setIsDeleting(false);
        return;
      }

      // Success - update graph locally (no refetch needed)
      try {
        // Remove node from cytoscape (also removes connected edges automatically)
        node.remove();

        // Remove from attribution cache
        if (updateAttributions) {
          updateAttributions({ remove: [nodeId] });
        }

        // Close tooltip
        if (onClose) {
          onClose();
        }
      } catch (localUpdateError) {
        // If local update fails, fall back to full refetch
        console.error('Local graph update failed, falling back to refetch:', localUpdateError);
        if (onGraphChange) {
          onGraphChange();
        }
        if (onClose) {
          onClose();
        }
      }
    } catch (err) {
      alert(`Error: ${err.message}`);
      setIsDeleting(false);
    }
  };

  if (!activeNodeTooltip || !cy) return null;

  const node = activeNodeTooltip.node;
  const nodeId = node.data('id');
  const nodeType = node.data('type'); // 'claim' or 'source'
  const nodeLabel = node.data('label');
  const nodeUrl = node.data('url'); // Only present on source nodes
  const clickOffset = activeNodeTooltip.clickOffset || { x: 0, y: 0 };

  // Determine entity type for attribution/comments
  const entityType = nodeType === 'source' ? 'source' : 'claim';

  // Check if current user is creator (for delete permission)
  const attribution = attributionsCache[nodeId];
  const isCreator = user && attribution?.creator?.username === user.username;

  // Get node dimensions in graph coordinates (use outerWidth/outerHeight for visual edges)
  const nodeOuterWidth = node.outerWidth();
  const nodeOuterHeight = node.outerHeight();

  // Node edge positions relative to node center (outerWidth/Height already includes padding/border)
  const nodeEdges = {
    left: -(nodeOuterWidth / 2),
    right: (nodeOuterWidth / 2),
    top: -(nodeOuterHeight / 2),
    bottom: (nodeOuterHeight / 2)
  };

  return (
    <>
      {/* Frame with node cutout */}
      <PositionedOverlay
        cytoElement={node}
        cy={cy}
        offset={{ x: nodeEdges.left - 24, y: nodeEdges.top - 24 }}
        passThrough={true}
      >
        {(() => {
          // Frame padding around node
          const padding = 20;
          const minContentWidth = 180; // Minimum to fit attribution + tabs
          const minExtension = 80;
          // Use measured content height with minimum fallback
          const bottomExtension = Math.max(minExtension, contentHeight + 10);
          const borderRadius = 8;
          // Total frame dimensions - use max of node width or minimum content width
          const contentWidth = Math.max(nodeOuterWidth, minContentWidth);
          const frameWidth = contentWidth + padding * 2;
          const frameHeight = nodeOuterHeight + padding * 2 + bottomExtension;
          // Cutout position (relative to frame top-left)
          const cutoutLeft = padding;
          const cutoutTop = padding;
          const cutoutRight = padding + nodeOuterWidth;

          // Animation start positions
          const startX = clickOffset.x / 2;
          const startY = clickOffset.y / 2;
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

          // Highlight dimensions (4px padding around frame)
          const highlightPadding = 4;
          const highlightWidth = frameWidth + highlightPadding * 2;
          const highlightHeight = frameHeight + highlightPadding * 2;
          // Highlight cutout must align with frame cutout in absolute position
          const highlightCutoutLeft = cutoutLeft + highlightPadding;
          const highlightCutoutTop = cutoutTop + highlightPadding;
          const highlightCutoutRight = cutoutRight + highlightPadding;
          const highlightCutoutBottom = cutoutBottom + highlightPadding;

          const highlightClipPath = `polygon(
            0% 0%, 100% 0%, 100% 100%, 0% 100%, 0% 0%,
            ${highlightCutoutLeft}px ${highlightCutoutTop}px,
            ${highlightCutoutLeft}px ${highlightCutoutBottom}px,
            ${highlightCutoutRight}px ${highlightCutoutBottom}px,
            ${highlightCutoutRight}px ${highlightCutoutTop}px,
            ${highlightCutoutLeft}px ${highlightCutoutTop}px
          )`;

          return (
            <div
              className="graph-tooltip-container"
              style={{
                '--start-x': `${startX}px`,
                '--start-y': `${startY}px`,
                pointerEvents: 'none'
              }}
            >
              <div
                className="graph-tooltip-highlight"
                style={{
                  width: `${highlightWidth}px`,
                  height: `${highlightHeight}px`,
                  clipPath: highlightClipPath,
                  borderRadius: `${borderRadius}px`,
                  pointerEvents: 'none'
                }}
              >
                <div style={{
                  width: `${frameWidth}px`,
                  height: `${frameHeight}px`,
                  backgroundColor: 'var(--node-default)',
                  clipPath: clipPath,
                  borderRadius: `${borderRadius}px`,
                  position: 'relative',
                  pointerEvents: 'none',
                  margin: `${highlightPadding}px`
                }}>
                  {/* Content area below the node cutout */}
                  <div
                    ref={contentRef}
                    className="graph-tooltip"
                    style={{
                      position: 'absolute',
                      top: `${cutoutBottom + 10}px`,
                      left: `${padding}px`,
                      right: `${padding}px`,
                      display: 'flex',
                      flexDirection: 'column',
                      pointerEvents: 'auto',
                      boxShadow: 'none',
                      minWidth: 'unset',
                      padding: 0
                    }}
                    onClick={(e) => e.stopPropagation()}
                  >
                    <div className="tooltip-content" style={{ flex: '1 1 auto' }}>
                      <div className="tooltip-attribution">
                        <UserAttribution entityUuid={nodeId} entityType={entityType} showTimestamp={true} />
                      </div>
                      {nodeType === 'source' && nodeUrl && (
                        <div><strong>URL:</strong> <a href={nodeUrl} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent-blue)' }}>{nodeUrl}</a></div>
                      )}
                      <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                        <button
                          onClick={() => setShowCreateModal(true)}
                          style={{
                            padding: '4px 8px',
                            fontSize: '11px',
                            cursor: 'pointer',
                            background: 'var(--bg-secondary)',
                            border: '1px solid var(--border-color)',
                            borderRadius: '4px'
                          }}
                        >
                          + Add Connected Node
                        </button>
                        {isCreator && (
                          <button
                            onClick={handleDelete}
                            disabled={isDeleting}
                            style={{
                              padding: '4px 8px',
                              fontSize: '11px',
                              cursor: isDeleting ? 'not-allowed' : 'pointer',
                              background: '#fee',
                              border: '1px solid #c88',
                              borderRadius: '4px',
                              color: '#a00',
                              opacity: isDeleting ? 0.5 : 1
                            }}
                          >
                            {isDeleting ? 'Deleting...' : 'Delete'}
                          </button>
                        )}
                      </div>
                    </div>
                    <div className="tooltip-comments-rating" style={{
                      marginLeft: `-${padding}px`,
                      marginRight: `-${padding}px`,
                      marginBottom: `-${padding}px`
                    }}>
                      <CommentsRating
                        entityUuid={nodeId}
                        entityType={entityType}   
                        onTabChange={setActiveTab}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        })()}
      </PositionedOverlay>
      <NodeCreationModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        node={node}
        cy={cy}
        existingNodeId={nodeId}
        existingNodeType={entityType}
        existingNodeLabel={nodeLabel}
        updateAttributions={updateAttributions}
        onGraphChange={onGraphChange}
      />
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

    // Use functional update to avoid re-render if same node
    setActiveNodeTooltip(prev => {
      if (prev && prev.node === node) {
        return prev; // Same object reference prevents effect re-run
      }
      return { node, clickOffset };
    });

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
