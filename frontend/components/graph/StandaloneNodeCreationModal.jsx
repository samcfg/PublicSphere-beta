import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createClaim, createSource } from '../../APInterface/api.js';
import { useAuth } from '../../utilities/AuthContext.jsx';
import '../../styles/components/modal.css';
import '../../styles/components/node-creation-panel.css';

/**
 * Modal for creating a standalone node (not connected to an existing node)
 * Used on the homepage to bootstrap new argument graphs
 *
 * @param {Object} props
 * @param {boolean} props.isOpen - Whether modal is visible
 * @param {Function} props.onClose - Close handler
 */
export function StandaloneNodeCreationModal({ isOpen, onClose }) {
  const navigate = useNavigate();
  const { user, token, isAuthenticated } = useAuth();
  const [nodeType, setNodeType] = useState(null); // 'claim' or 'source'
  const [content, setContent] = useState('');
  const [title, setTitle] = useState(''); // For sources - required
  const [url, setUrl] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleCreate = async () => {
    // Validation
    if (!nodeType || !content.trim()) return;

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

        // Handle duplicate errors
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

      // Get the new node ID
      const newNodeId = nodeResult.data.uuid || nodeResult.data.id || nodeResult.data.node_id;
      if (!newNodeId) {
        console.error('Node creation response:', nodeResult.data);
        throw new Error('Could not get ID from created node');
      }

      // Success - navigate to the new node's context view
      handleClose();
      navigate(`/context?id=${newNodeId}`);

    } catch (err) {
      setError(err.message || 'Failed to create node');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    // Reset form state
    setNodeType(null);
    setContent('');
    setTitle('');
    setUrl('');
    setError(null);
    onClose();
  };

  const canSubmit = nodeType && content.trim()
    && (nodeType !== 'source' || title.trim()) // Source requires title
    && !isSubmitting;

  return (
    <div className="modal-backdrop" onClick={handleClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ width: '500px', alignItems: 'stretch' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 className="modal-title" style={{ margin: 0 }}>Create Node</h2>
          <button
            onClick={handleClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '24px',
              cursor: 'pointer',
              color: 'var(--modal-text)',
              padding: '0',
              lineHeight: '1',
              opacity: '0.6'
            }}
          >
            &times;
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', width: '100%' }}>
          {/* Step 1: Node type selection */}
          <div className="node-creation-field">
            <label className="node-creation-label">What are you creating?</label>
            <div className="node-creation-type-buttons">
              <button
                className={`node-creation-type-btn ${nodeType === 'claim' ? 'selected' : ''}`}
                onClick={() => setNodeType('claim')}
              >
                Claim
              </button>
              <button
                className={`node-creation-type-btn ${nodeType === 'source' ? 'selected' : ''}`}
                onClick={() => setNodeType('source')}
              >
                Evidence
              </button>
            </div>
          </div>

          {/* Step 2: Content fields */}
          {nodeType && (
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
                  style={{ minHeight: '120px' }}
                />
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

        <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', width: '100%' }}>
          <button className="modal-button" onClick={handleClose}>
            Cancel
          </button>
          <button
            className="modal-button"
            style={{
              background: canSubmit ? 'var(--accent-green)' : 'transparent',
              borderColor: canSubmit ? 'var(--accent-green)' : 'var(--modal-border)',
              color: canSubmit ? '#000' : 'var(--modal-text)',
              opacity: canSubmit ? 1 : 0.4,
              cursor: canSubmit ? 'pointer' : 'not-allowed'
            }}
            disabled={!canSubmit}
            onClick={handleCreate}
          >
            {isSubmitting ? 'Creating...' : 'Create'}
          </button>
        </div>
      </div>
    </div>
  );
}
