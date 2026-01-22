import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PositionedOverlay } from './PositionedOverlay.jsx';
import { UserAttribution } from '../common/UserAttribution.jsx';
import { CommentsRating } from '../common/CommentsRating.jsx';
import { useAuth } from '../../utilities/AuthContext.jsx';
import { useAttributions } from '../../utilities/AttributionContext.jsx';
import { deleteConnection, updateConnection } from '../../APInterface/api.js';
import { FaMagnifyingGlassArrowRight } from "react-icons/fa6";
import { FaRegEdit } from "react-icons/fa";
import { MdDelete } from "react-icons/md";

/**
 * Edge tooltip component that displays edge data on click
 * Shows attribution, logic type, and notes
 *
 * @param {Object} props
 * @param {Object} props.activeEdgeTooltip - {edge: cytoscapeEdge, clickOffset: {x, y}} or null
 * @param {Object} props.cy - Cytoscape instance
 * @param {Function} props.updateAttributions - Function to update attribution cache locally
 * @param {Function} props.onGraphChange - Fallback callback for complex graph changes
 * @param {Function} props.onClose - Callback to close the tooltip
 */
export function OnClickEdge({ activeEdgeTooltip, cy, updateAttributions, onGraphChange, onClose }) {
  const { token } = useAuth();
  const attributionsCache = useAttributions();
  const navigate = useNavigate();
  const [showEditModal, setShowEditModal] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isEditSubmitting, setIsEditSubmitting] = useState(false);
  const [editNotes, setEditNotes] = useState('');

  if (!activeEdgeTooltip || !cy) return null;

  const edge = activeEdgeTooltip.edge;
  const edgeId = edge.data('id');
  const logicType = edge.data('logic_type');
  const notes = edge.data('notes');
  const clickOffset = activeEdgeTooltip.clickOffset || { x: 0, y: 0 };

  // Check if current user is creator (for edit/delete permission)
  const attribution = attributionsCache[edgeId];
  const isCreator = attribution?.creator?.is_own === true;

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

  // Delete handler
  const handleDelete = async () => {
    if (!token || !activeEdgeTooltip) return;
    if (!confirm('Delete this connection? This cannot be undone.')) return;

    setIsDeleting(true);
    try {
      const result = await deleteConnection(token, edgeId);

      if (result.error) {
        alert(`Failed to delete: ${result.error}`);
        setIsDeleting(false);
        return;
      }

      // Success - update graph locally
      try {
        edge.remove();

        // Remove from attribution cache
        if (updateAttributions) {
          updateAttributions({ remove: [edgeId] });
        }

        // Close tooltip
        if (onClose) {
          onClose();
        }
      } catch (localUpdateError) {
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

  // Edit handler
  const handleEditSubmit = async () => {
    setIsEditSubmitting(true);
    try {
      const result = await updateConnection(token, edgeId, { notes: editNotes.trim() });

      if (result.error) {
        alert(`Failed to update: ${result.error}`);
        setIsEditSubmitting(false);
        return;
      }

      // Success: update cytoscape edge
      edge.data('notes', editNotes.trim());

      // Close modal
      setShowEditModal(false);
      setIsEditSubmitting(false);
    } catch (err) {
      alert(`Error: ${err.message}`);
      setIsEditSubmitting(false);
    }
  };

  const handleEditClick = () => {
    setEditNotes(notes || '');
    setShowEditModal(true);
  };

  return (
    <>
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
                  <div style={{ marginLeft: 'auto', display: 'flex', gap: '6px', alignItems: 'center' }}>
                    <FaMagnifyingGlassArrowRight
                      onClick={() => navigate(`/connectionview?id=${edgeId}`)}
                      style={{ cursor: 'pointer', fontSize: '16px' }}
                      title="Expand view"
                    />
                    {isCreator && (
                      <FaRegEdit
                        onClick={handleEditClick}
                        style={{ cursor: 'pointer', fontSize: '14px' }}
                        title="Edit connection"
                      />
                    )}
                    {isCreator && (
                      <MdDelete
                        onClick={handleDelete}
                        style={{
                          cursor: isDeleting ? 'not-allowed' : 'pointer',
                          fontSize: '16px',
                          color: '#e74c3c',
                          opacity: isDeleting ? 0.5 : 1
                        }}
                        title="Delete connection"
                      />
                    )}
                  </div>
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
      {/* Edit Modal */}
      {showEditModal && (
        <>
          {/* Backdrop */}
          <div
            onClick={() => setShowEditModal(false)}
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(0, 0, 0, 0.5)',
              zIndex: 9999
            }}
          />
          {/* Modal */}
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              position: 'fixed',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              zIndex: 10000,
              backgroundColor: 'var(--bg-secondary)',
              border: '2px solid var(--border-color)',
              borderRadius: '8px',
              padding: '24px',
              minWidth: '400px',
              maxWidth: '600px'
            }}>
            <h3 style={{ marginTop: 0, marginBottom: '16px', color: 'var(--text-primary)' }}>
              Edit Connection Notes
            </h3>
            <textarea
              value={editNotes}
              onChange={(e) => setEditNotes(e.target.value)}
              placeholder="Add notes about this connection..."
              style={{
                width: '100%',
                minHeight: '120px',
                padding: '8px',
                fontSize: '14px',
                fontFamily: 'inherit',
                backgroundColor: 'var(--bg-primary)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-color)',
                borderRadius: '4px',
                resize: 'vertical'
              }}
            />
            <div style={{ marginTop: '16px', display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowEditModal(false)}
                style={{
                  padding: '8px 16px',
                  fontSize: '14px',
                  cursor: 'pointer',
                  backgroundColor: 'var(--bg-primary)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '4px'
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleEditSubmit}
                disabled={isEditSubmitting}
                style={{
                  padding: '8px 16px',
                  fontSize: '14px',
                  cursor: isEditSubmitting ? 'not-allowed' : 'pointer',
                  backgroundColor: 'var(--accent-blue)',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '4px',
                  opacity: isEditSubmitting ? 0.5 : 1
                }}
              >
                {isEditSubmitting ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </>
      )}
    </>
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
