import { useState } from 'react';
import { PositionedOverlay } from './PositionedOverlay.jsx';
import { createClaim, createSource, createConnection } from '../../APInterface/api.js';
import { useAuth } from '../../utilities/AuthContext.jsx';
import '../../styles/components/node-creation-panel.css';

/**
 * Node-styled panel for creating a new node connected to an existing node
 *
 * @param {Object} props
 * @param {boolean} props.isOpen - Whether panel is visible
 * @param {Function} props.onClose - Close handler
 * @param {Object} props.node - Cytoscape node element
 * @param {Object} props.cy - Cytoscape instance
 * @param {string} props.existingNodeId - UUID of node to connect to
 * @param {string} props.existingNodeType - 'claim' or 'source'
 * @param {string} props.existingNodeLabel - Text content of existing node
 * @param {Function} props.updateAttributions - Function to update attribution cache locally
 * @param {Function} props.onGraphChange - Fallback callback for complex graph changes
 */
export function NodeCreationModal({ isOpen, onClose, node, cy, existingNodeId, existingNodeType, existingNodeLabel, updateAttributions, onGraphChange }) {
  const { user, token, isAuthenticated } = useAuth();
  const [nodeType, setNodeType] = useState(null); // 'claim' or 'source'
  const [relationship, setRelationship] = useState(null); // 'supports', 'contradicts'
  const [content, setContent] = useState('');
  const [title, setTitle] = useState(''); // For sources - required
  const [url, setUrl] = useState('');
  const [connectionNotes, setConnectionNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen || !node || !cy) return null;

  // Truncate label for display
  const truncatedLabel = existingNodeLabel
    ? (existingNodeLabel.length > 50 ? existingNodeLabel.slice(0, 50) + '...' : existingNodeLabel)
    : existingNodeId.slice(0, 8);

  // Position to the right of the node
  const nodeWidth = node.outerWidth();
  const offsetX = nodeWidth / 2 + 40; // Right edge of node + gap

  // Determine valid relationships based on node types
  const getRelationshipOptions = () => {
    if (nodeType === 'source' && existingNodeType === 'claim') {
      // Adding evidence to a claim
      return [
        { value: 'supports', label: 'supports', desc: 'this claim' },
        { value: 'contradicts', label: 'contradicts', desc: 'this claim' }
      ];
    } else if (nodeType === 'claim' && existingNodeType === 'source') {
      // Adding claim from evidence
      return [
        { value: 'follows', label: 'follows from', desc: 'this evidence' }
      ];
    } else if (nodeType === 'claim' && existingNodeType === 'claim') {
      // Adding claim to claim
      return [
        { value: 'supports', label: 'supports', desc: 'this claim' },
        { value: 'contradicts', label: 'contradicts', desc: 'this claim' },
        { value: 'implied', label: 'is implied by', desc: 'this claim' }
      ];
    }
    return [];
  };

  // Determine connection direction based on relationship
  const getConnectionData = (newNodeId) => {
    // Default: new node points to existing (new supports/contradicts existing)
    let fromId = newNodeId;
    let toId = existingNodeId;

    // Reverse direction for "follows from" and "is implied by"
    if (relationship === 'follows' || relationship === 'implied') {
      fromId = existingNodeId;
      toId = newNodeId;
    }

    // Map relationship to logic_type
    // null/omitted = supports (default display)
    // NOT = contradicts
    const connectionData = {
      from_node_id: fromId,
      to_node_id: toId,
      notes: connectionNotes.trim()
    };

    if (relationship === 'contradicts') {
      connectionData.logic_type = 'NOT';
    }
    // For 'supports', 'follows', 'implied' - omit logic_type (defaults to supports)

    return connectionData;
  };

  const handleCreate = async () => {
    // Validation
    if (!nodeType || !relationship || !content.trim() || !connectionNotes.trim()) return;

    // Source-specific validation: title is required
    if (nodeType === 'source' && !title.trim()) {
      setError('Source title is required');
      return;
    }

    if (!isAuthenticated || !token) {
      setError('You must be logged in to create nodes');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      // Step 1: Create the node
      let nodeResult;
      if (nodeType === 'claim') {
        nodeResult = await createClaim(token, { content: content.trim() });
      } else {
        nodeResult = await createSource(token, {
          title: title.trim(),
          content: content.trim(),
          url: url.trim() || null
        });
      }

      if (nodeResult.error) {
        // Handle title_required error specifically
        if (nodeResult.error === 'title_required') {
          setError('Source title is required');
          setIsSubmitting(false);
          return;
        }

        // Handle duplicate errors - All phases

        // Claim duplicates (Phase 2)
        if (nodeResult.error === 'duplicate_exact' || nodeResult.error === 'duplicate_similar') {
          const label = nodeResult.error === 'duplicate_exact'
            ? 'This claim already exists'
            : 'This claim is very similar to an existing one';
          const existingContent = nodeResult.data?.existing_content || '';
          const existingId = nodeResult.data?.existing_node_id;
          const similarity = nodeResult.data?.similarity_score;

          setError(
            <div className="duplicate-error">
              <strong>{label}</strong>
              <p style={{ fontStyle: 'italic', margin: '8px 0', fontSize: '14px' }}>
                {existingContent.slice(0, 150)}{existingContent.length > 150 ? '...' : ''}
              </p>
              {similarity && (
                <small style={{ opacity: 0.7 }}>Similarity: {(similarity * 100).toFixed(0)}%</small>
              )}
              {existingId && (
                <a
                  href={`/context?id=${existingId}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: 'var(--accent-blue)', textDecoration: 'underline', display: 'block', marginTop: '8px' }}
                >
                  View existing claim →
                </a>
              )}
            </div>
          );
          setIsSubmitting(false);
          return;
        }

        // Source URL duplicate (Phase 1)
        if (nodeResult.error === 'duplicate_url') {
          const existingTitle = nodeResult.data?.existing_title || 'Unknown';
          const existingId = nodeResult.data?.existing_node_id;
          setError(
            <div className="duplicate-error">
              <strong>This URL already exists</strong>
              <p style={{ fontStyle: 'italic', margin: '8px 0' }}>{existingTitle}</p>
              {existingId && (
                <a
                  href={`/context?id=${existingId}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: 'var(--accent-blue)', textDecoration: 'underline' }}
                >
                  View existing source →
                </a>
              )}
            </div>
          );
          setIsSubmitting(false);
          return;
        }

        // Source title duplicates (Phase 2)
        if (nodeResult.error === 'duplicate_title_exact' || nodeResult.error === 'duplicate_title_similar') {
          const label = nodeResult.error === 'duplicate_title_exact'
            ? 'A source with this title already exists'
            : 'A source with a very similar title exists';
          const existingTitle = nodeResult.data?.existing_title || 'Unknown';
          const existingId = nodeResult.data?.existing_node_id;
          const similarity = nodeResult.data?.similarity_score;

          setError(
            <div className="duplicate-error">
              <strong>{label}</strong>
              <p style={{ fontStyle: 'italic', margin: '8px 0' }}>{existingTitle}</p>
              {similarity && (
                <small style={{ opacity: 0.7 }}>Similarity: {(similarity * 100).toFixed(0)}%</small>
              )}
              {existingId && (
                <a
                  href={`/context?id=${existingId}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: 'var(--accent-blue)', textDecoration: 'underline', display: 'block', marginTop: '8px' }}
                >
                  View existing source →
                </a>
              )}
            </div>
          );
          setIsSubmitting(false);
          return;
        }

        const errMsg = typeof nodeResult.error === 'object'
          ? JSON.stringify(nodeResult.error)
          : nodeResult.error;
        throw new Error(errMsg);
      }

      // Get the new node ID - try common field names
      const newNodeId = nodeResult.data.uuid || nodeResult.data.id || nodeResult.data.node_id;
      if (!newNodeId) {
        console.error('Node creation response:', nodeResult.data);
        throw new Error('Could not get ID from created node');
      }

      // Step 2: Create the connection
      const connectionData = getConnectionData(newNodeId);
      const connResult = await createConnection(token, connectionData);

      if (connResult.error) {
        const errMsg = typeof connResult.error === 'object'
          ? JSON.stringify(connResult.error)
          : connResult.error;
        throw new Error(errMsg);
      }

      // Success - add to graph locally (no refetch needed)
      try {
        // Add new node to cytoscape
        cy.add({
          data: {
            id: newNodeId,
            label: nodeType === 'source' ? 'Source' : 'Claim',
            content: content.trim(),
            type: nodeType,
            ...(nodeType === 'source' && url.trim() ? { url: url.trim() } : {})
          }
        });

        // Add new edge to cytoscape
        const { from_node_id, to_node_id, logic_type } = connectionData;
        cy.add({
          data: {
            id: connResult.data?.id || connResult.data?.uuid || `${from_node_id}-${to_node_id}`,
            source: from_node_id,
            target: to_node_id,
            ...(logic_type ? { logic_type } : {})
          }
        });

        // Run layout to position new node
        cy.layout({
          name: 'dagre',
          rankDir: 'BT',
          nodeSep: 80,
          rankSep: 120,
          animate: false
        }).run();

        // Add attribution to cache (current user is creator)
        if (updateAttributions && user) {
          updateAttributions({
            add: {
              [newNodeId]: {
                creator: {
                  entity_uuid: newNodeId,
                  entity_type: nodeType,
                  username: user.username,
                  timestamp: new Date().toISOString(),
                  is_anonymous: false
                },
                editors: []
              }
            }
          });
        }

        handleClose();
      } catch (localUpdateError) {
        // If local update fails, fall back to full refetch
        console.error('Local graph update failed, falling back to refetch:', localUpdateError);
        if (onGraphChange) {
          onGraphChange();
        }
        handleClose();
      }

    } catch (err) {
      setError(err.message || 'Failed to create node');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    // Reset form state
    setNodeType(null);
    setRelationship(null);
    setContent('');
    setTitle('');
    setUrl('');
    setConnectionNotes('');
    setError(null);
    onClose();
  };

  const relationshipOptions = getRelationshipOptions();
  // Validate: for sources, title is required
  const canSubmit = nodeType && relationship && content.trim() && connectionNotes.trim()
    && (nodeType !== 'source' || title.trim()) // Source requires title
    && !isSubmitting;

  return (
    <PositionedOverlay
      cytoElement={node}
      cy={cy}
      offset={{ x: offsetX, y: -100 }}
    >
      <div className="node-creation-panel" onClick={(e) => e.stopPropagation()}>
      <div className="node-creation-highlight">
        <div className="node-creation-inner">
          <div className="node-creation-header">
            <h2 className="node-creation-title">Add Node</h2>
            <button className="node-creation-close" onClick={onClose}>
              &times;
            </button>
          </div>

          <div className="node-creation-context">
            Connecting to {existingNodeType}: <strong>{truncatedLabel}</strong>
          </div>

          <div className="node-creation-content">
            {/* Step 1: Node type selection */}
            <div className="node-creation-field">
              <label className="node-creation-label">What are you adding?</label>
              <div className="node-creation-type-buttons">
                <button
                  className={`node-creation-type-btn ${nodeType === 'source' ? 'selected' : ''}`}
                  onClick={() => { setNodeType('source'); setRelationship(null); }}
                >
                  Evidence
                </button>
                <button
                  className={`node-creation-type-btn ${nodeType === 'claim' ? 'selected' : ''}`}
                  onClick={() => { setNodeType('claim'); setRelationship(null); }}
                >
                  Claim
                </button>
              </div>
            </div>

            {/* Step 2: Relationship selection */}
            {nodeType && relationshipOptions.length > 0 && (
              <div className="node-creation-field">
                <label className="node-creation-label">Relationship</label>
                <div className="node-creation-options">
                  {relationshipOptions.map(opt => (
                    <label key={opt.value} className="node-creation-option">
                      <input
                        type="radio"
                        name="relationship"
                        value={opt.value}
                        checked={relationship === opt.value}
                        onChange={() => setRelationship(opt.value)}
                      />
                      <span>This <em>{opt.label}</em> {opt.desc}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* Step 3: Content fields */}
            {nodeType && relationship && (
              <>
                {nodeType === 'source' && (
                  <>
                    <div className="node-creation-field">
                      <label className="node-creation-label">
                        Title <span style={{ color: '#ff4444' }}>*</span>
                      </label>
                      <input
                        type="text"
                        className={`node-creation-input ${nodeType === 'source' && !title.trim() ? 'error' : ''}`}
                        placeholder="Source title (required)"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        required
                      />
                    </div>
                    <div className="node-creation-field">
                      <label className="node-creation-label">URL (optional)</label>
                      <input
                        type="url"
                        className="node-creation-input"
                        placeholder="https://..."
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                      />
                    </div>
                  </>
                )}
                <div className="node-creation-field">
                  <label className="node-creation-label">
                    {nodeType === 'source' ? 'Description' : 'Claim'}
                  </label>
                  <textarea
                    className="node-creation-textarea"
                    placeholder={nodeType === 'source' ? 'Describe the evidence...' : 'State the claim...'}
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                  />
                </div>
                <div className="node-creation-field">
                  <label className="node-creation-label">
                    Connection Notes
                    <span style={{ fontSize: '12px', opacity: 0.7, marginLeft: '8px' }}>
                      (max 500 chars)
                    </span>
                  </label>
                  <textarea
                    className="node-creation-textarea node-creation-notes"
                    placeholder="Explain why this connection holds..."
                    value={connectionNotes}
                    onChange={(e) => {
                      if (e.target.value.length <= 500) {
                        setConnectionNotes(e.target.value);
                      }
                    }}
                    maxLength={500}
                  />
                  <div style={{ fontSize: '11px', opacity: 0.6, textAlign: 'right', marginTop: '4px' }}>
                    {connectionNotes.length}/500
                  </div>
                </div>
              </>
            )}

            {/* Error display */}
            {error && (
              <div className="node-creation-error">
                {error}
              </div>
            )}
          </div>

          <div className="node-creation-footer">
            <button className="node-creation-btn" onClick={handleClose}>
              Cancel
            </button>
            <button
              className="node-creation-btn node-creation-btn-primary"
              disabled={!canSubmit}
              onClick={handleCreate}
            >
              {isSubmitting ? 'Creating...' : 'Create'}
            </button>
          </div>
        </div>
      </div>
      </div>
    </PositionedOverlay>
  );
}
