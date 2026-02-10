import { useState, useRef, useEffect } from 'react';
import { NodeBox } from './NodeBox.jsx';
import { createSuggestion } from '../../APInterface/api.js';
import { useAuth } from '../../utilities/AuthContext.jsx';

/**
 * SuggestEditModal - Modal for suggesting edits to entities
 * Wraps NodeBox for nodes or shows textarea for connections
 *
 * @param {Object} props
 * @param {boolean} props.isOpen - Whether modal is open
 * @param {Function} props.onClose - Callback to close modal
 * @param {string} props.nodeId - UUID of target entity (node or connection)
 * @param {string} props.nodeType - 'claim' | 'source' | 'connection'
 * @param {Object} props.initialData - Current entity data (node format or {notes: string} for connection)
 * @param {Object} props.sourceData - Full source metadata (if source node, null for connections)
 */
export function SuggestEditModal({ isOpen, onClose, nodeId, nodeType, initialData, sourceData }) {
  const { token } = useAuth();
  const nodeBoxRef = useRef(null);

  const [rationale, setRationale] = useState('');
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // For connection type - direct notes editing
  const [connectionNotes, setConnectionNotes] = useState('');

  // Reset state when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setRationale('');
      setIsAnonymous(false);
      setError(null);
      setSuccess(null);
      // Initialize connection notes if it's a connection type
      if (nodeType === 'connection') {
        setConnectionNotes(initialData?.notes || '');
      }
    }
  }, [isOpen, nodeType, initialData]);

  // Validation: rationale must be at least 20 chars
  const rationaleValid = rationale.trim().length >= 20;
  const isValid = rationaleValid;

  const handleSubmit = async () => {
    if (!isValid) return;

    // For nodes, check if nodeBoxRef exists
    if (nodeType !== 'connection' && !nodeBoxRef.current) return;

    setIsSubmitting(true);
    setError(null);

    try {
      // Build proposed_changes object
      let proposedChanges = {};

      if (nodeType === 'connection') {
        // For connections, only 'notes' can be edited
        if (connectionNotes !== undefined && connectionNotes !== null) {
          proposedChanges.notes = connectionNotes;
        }
      } else {
        // Get data from NodeBox for nodes
        const nodeBoxData = nodeBoxRef.current.getData();

        // If user selected different node during edit, that's not allowed for suggestions
        if (nodeBoxData.inputMode === 'selected') {
          setError('Cannot suggest switching to an existing node. Please modify the current node fields.');
          setIsSubmitting(false);
          return;
        }

        if (nodeType === 'source') {
        // Extract all source fields that might have changed
        const sourceFields = [
          'title', 'url', 'content', 'source_type', 'authors', 'doi',
          'publication_date', 'container_title', 'publisher', 'publisher_location',
          'volume', 'issue', 'pages', 'edition', 'isbn', 'issn', 'arxiv_id',
          'thumbnail_link', 'accessed_date', 'excerpt', 'editors',
          'jurisdiction', 'legal_category', 'court', 'decision_date',
          'case_name', 'code', 'section', 'metadata'
        ];

        sourceFields.forEach(field => {
          if (nodeBoxData[field] !== undefined && nodeBoxData[field] !== null && nodeBoxData[field] !== '') {
            // Convert camelCase to snake_case for backend
            const snakeField = field.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
            proposedChanges[snakeField] = nodeBoxData[field];
          }
        });
        } else {
          // Claim only has content
          if (nodeBoxData.content) {
            proposedChanges.content = nodeBoxData.content;
          }
        }
      }

      // Check if any changes were made
      if (Object.keys(proposedChanges).length === 0) {
        setError('No changes detected. Please modify at least one field.');
        setIsSubmitting(false);
        return;
      }

      // Submit suggestion
      const result = await createSuggestion(token, {
        entity_uuid: nodeId,
        entity_type: nodeType,
        proposed_changes: proposedChanges,
        rationale: rationale.trim(),
        is_anonymous: isAnonymous
      });

      if (result.error) {
        setError(result.error);
        setIsSubmitting(false);
        return;
      }

      // Success!
      const suggestionId = result.data?.suggestion_id;
      setSuccess(suggestionId);
      setIsSubmitting(false);

      // Close modal after 2 seconds
      setTimeout(() => {
        onClose();
      }, 2000);

    } catch (err) {
      setError(err.message || 'Failed to submit suggestion');
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  // Success view
  if (success) {
    return (
      <>
        {/* Backdrop */}
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.6)',
            zIndex: 9999
          }}
        />
        {/* Success Message */}
        <div style={{
          position: 'fixed',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          zIndex: 10000,
          backgroundColor: 'var(--bg-primary)',
          padding: '40px',
          borderRadius: '8px',
          border: '2px solid #10b981',
          maxWidth: '500px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>✓</div>
          <h3 style={{ marginBottom: '12px', color: 'var(--text-primary)' }}>
            Suggestion Submitted!
          </h3>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '8px' }}>
            Your suggestion has been submitted for community review.
          </p>
          <p style={{
            color: 'var(--text-muted)',
            fontSize: '12px',
            fontFamily: 'monospace'
          }}>
            ID: {success}
          </p>
        </div>
      </>
    );
  }

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.6)',
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
          backgroundColor: 'var(--bg-primary)',
          borderRadius: '8px',
          maxWidth: '700px',
          maxHeight: '90vh',
          width: '90%',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          border: '2px solid #d97706',
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.3)'
        }}
      >
        {/* Header */}
        <div style={{
          padding: '24px 24px 16px',
          borderBottom: '1px solid var(--border-color)',
          backgroundColor: 'rgba(217, 119, 6, 0.05)'
        }}>
          <h3 style={{
            margin: '0 0 12px 0',
            fontSize: '20px',
            fontWeight: '600',
            color: '#d97706'
          }}>
            Suggest an Edit
          </h3>
          <p style={{
            margin: 0,
            fontSize: '13px',
            color: 'var(--text-secondary)',
            lineHeight: '1.5'
          }}>
            {nodeType === 'connection'
              ? "Suggest improvements to the connection's textual explanation. To argue about the logic type or strength, rate or comment instead."
              : "Modifications are for improving the overall quality of a node's writing. To argue about its content, rate or comment instead."
            }
          </p>
        </div>

        {/* Scrollable Content */}
        <div style={{
          flex: '1 1 auto',
          overflowY: 'auto',
          padding: '20px 24px'
        }}>
          {nodeType === 'connection' ? (
            /* Connection Notes Editor */
            <div>
              <label style={{
                display: 'block',
                fontSize: '13px',
                fontWeight: '600',
                color: 'var(--text-primary)',
                marginBottom: '8px'
              }}>
                Connection Notes
              </label>
              <textarea
                value={connectionNotes}
                onChange={(e) => setConnectionNotes(e.target.value)}
                placeholder="Edit the textual explanation for this connection..."
                style={{
                  width: '100%',
                  minHeight: '200px',
                  padding: '12px',
                  fontSize: '14px',
                  lineHeight: '1.5',
                  border: '1px solid var(--border-color)',
                  borderRadius: '4px',
                  backgroundColor: 'var(--bg-secondary)',
                  color: 'var(--text-primary)',
                  resize: 'vertical',
                  fontFamily: 'inherit'
                }}
              />
            </div>
          ) : (
            /* NodeBox Form for claims and sources */
            <NodeBox
              ref={nodeBoxRef}
              mode="edit"
              initialData={{
                nodeType: nodeType,
                content: initialData?.content || '',
                title: nodeType === 'source' ? initialData?.title : '',
                url: initialData?.url || '',
                ...(nodeType === 'source' && sourceData ? {
                  sourceType: sourceData.source_type || '',
                  authors: sourceData.authors || [],
                  doi: sourceData.doi || '',
                  publicationDate: sourceData.publication_date || '',
                  containerTitle: sourceData.container_title || '',
                  publisher: sourceData.publisher || '',
                  volume: sourceData.volume || '',
                  issue: sourceData.issue || '',
                  pages: sourceData.pages || '',
                  edition: sourceData.edition || '',
                  isbn: sourceData.isbn || '',
                  issn: sourceData.issn || '',
                  arxivId: sourceData.arxiv_id || ''
                } : {})
              }}
              showControls={false}
            />
          )}

          {/* Rationale Section */}
          <div style={{ marginTop: '24px' }}>
            <label style={{
              display: 'block',
              fontSize: '13px',
              fontWeight: '600',
              color: 'var(--text-primary)',
              marginBottom: '8px'
            }}>
              Rationale <span style={{ color: '#d97706' }}>*</span>
            </label>
            <textarea
              value={rationale}
              onChange={(e) => setRationale(e.target.value)}
              placeholder="Why does this change improve clarity, accuracy, or completeness?"
              style={{
                width: '100%',
                minHeight: '100px',
                padding: '12px',
                fontSize: '14px',
                lineHeight: '1.5',
                border: `1px solid ${rationaleValid ? 'var(--border-color)' : '#ef4444'}`,
                borderRadius: '4px',
                backgroundColor: 'var(--bg-secondary)',
                color: 'var(--text-primary)',
                resize: 'vertical',
                fontFamily: 'inherit'
              }}
            />
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginTop: '6px',
              fontSize: '12px'
            }}>
              <span style={{
                color: rationaleValid ? 'var(--text-muted)' : '#ef4444'
              }}>
                {rationaleValid ? '✓ Valid' : `Minimum 20 characters (${rationale.trim().length}/20)`}
              </span>
              <span style={{ color: 'var(--text-muted)' }}>
                {rationale.length}/2000
              </span>
            </div>
          </div>

          {/* Anonymous Option */}
          <label style={{
            display: 'flex',
            alignItems: 'center',
            marginTop: '16px',
            fontSize: '13px',
            color: 'var(--text-primary)',
            cursor: 'pointer'
          }}>
            <input
              type="checkbox"
              checked={isAnonymous}
              onChange={(e) => setIsAnonymous(e.target.checked)}
              style={{ marginRight: '8px' }}
            />
            Submit anonymously
          </label>

          {/* Error Display */}
          {error && (
            <div style={{
              marginTop: '16px',
              padding: '12px',
              backgroundColor: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid #ef4444',
              borderRadius: '4px',
              fontSize: '13px',
              color: '#ef4444'
            }}>
              {typeof error === 'string' ? error : JSON.stringify(error)}
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{
          padding: '16px 24px',
          borderTop: '1px solid var(--border-color)',
          display: 'flex',
          justifyContent: 'flex-end',
          gap: '12px',
          backgroundColor: 'var(--bg-secondary)'
        }}>
          <button
            onClick={onClose}
            disabled={isSubmitting}
            style={{
              padding: '10px 20px',
              fontSize: '14px',
              fontWeight: '500',
              cursor: isSubmitting ? 'not-allowed' : 'pointer',
              border: '1px solid var(--border-color)',
              borderRadius: '4px',
              backgroundColor: 'var(--bg-primary)',
              color: 'var(--text-primary)',
              opacity: isSubmitting ? 0.5 : 1
            }}
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!isValid || isSubmitting}
            style={{
              padding: '10px 20px',
              fontSize: '14px',
              fontWeight: '500',
              cursor: (!isValid || isSubmitting) ? 'not-allowed' : 'pointer',
              border: 'none',
              borderRadius: '4px',
              backgroundColor: isValid && !isSubmitting ? '#d97706' : '#9ca3af',
              color: 'white',
              opacity: (!isValid || isSubmitting) ? 0.6 : 1
            }}
          >
            {isSubmitting ? 'Submitting...' : 'Submit for Community Review'}
          </button>
        </div>
      </div>
    </>
  );
}
