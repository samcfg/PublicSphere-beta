import { forwardRef } from 'react';
import '../../styles/components/node-creation-panel.css';

/**
 * Node creation box - positioned to the right of connection box
 * Shows node type selector and content fields
 * Highlight color reflects node type (claim=blue, source=green)
 *
 * @param {Object} props
 * @param {number} props.index - Index of this node box (for compound connections)
 * @param {string} props.nodeType - Selected node type ('claim' or 'source')
 * @param {Function} props.onNodeTypeChange - Callback when type changes
 * @param {string} props.content - Node content text
 * @param {Function} props.onContentChange - Callback when content changes
 * @param {string} props.title - Source title (sources only)
 * @param {Function} props.onTitleChange - Callback when title changes
 * @param {string} props.url - Source URL (sources only)
 * @param {Function} props.onUrlChange - Callback when URL changes
 * @param {Function} props.onClose - Close/cancel callback (only shown on first box)
 * @param {Function} props.onSubmit - Submit/create callback (only shown on first box)
 * @param {boolean} props.canSubmit - Whether submit button is enabled
 * @param {boolean} props.isSubmitting - Whether currently submitting
 * @param {React.ReactNode} props.error - Error message to display
 * @param {boolean} props.showControls - Whether to show close/submit buttons (only first box)
 * @param {React.Ref} ref - Forwarded ref for height measurement
 */
export const NodeBox = forwardRef(({
  index = 0,
  nodeType,
  onNodeTypeChange,
  content,
  onContentChange,
  title,
  onTitleChange,
  url,
  onUrlChange,
  onClose,
  onSubmit,
  canSubmit,
  isSubmitting,
  error,
  showControls = true
}, ref) => {
  // Determine highlight color based on node type
  const getHighlightColor = () => {
    if (!nodeType) return 'var(--accent-blue)'; // Default neutral
    if (nodeType === 'source') return 'var(--accent-green)';
    return 'var(--accent-blue)'; // claim
  };

  return (
    <div ref={ref} className="node-creation-panel" onClick={(e) => e.stopPropagation()}>
      <div className="node-creation-highlight" style={{ backgroundColor: getHighlightColor() }}>
        <div className="node-creation-inner">
          <div className="node-creation-header">
            <h2 className="node-creation-title" style={{ color: getHighlightColor() }}>
              {index > 0 ? `Node ${index + 1}` : 'New Node'}
            </h2>
            {showControls && (
              <button className="node-creation-close" onClick={onClose}>
                &times;
              </button>
            )}
          </div>

          <div className="node-creation-content">
            {/* Node type selection */}
            <div className="node-creation-field">
              <label className="node-creation-label">What are you adding?</label>
              <div className="node-creation-type-buttons">
                <button
                  className={`node-creation-type-btn ${nodeType === 'source' ? 'selected' : ''}`}
                  onClick={() => onNodeTypeChange('source')}
                  style={{
                    backgroundColor: nodeType === 'source' ? 'var(--accent-green)' : 'transparent',
                    borderColor: nodeType === 'source' ? 'var(--accent-green)' : 'var(--attr-border)'
                  }}
                >
                  Evidence
                </button>
                <button
                  className={`node-creation-type-btn ${nodeType === 'claim' ? 'selected' : ''}`}
                  onClick={() => onNodeTypeChange('claim')}
                  style={{
                    backgroundColor: nodeType === 'claim' ? 'var(--accent-blue)' : 'transparent',
                    borderColor: nodeType === 'claim' ? 'var(--accent-blue)' : 'var(--attr-border)'
                  }}
                >
                  Claim
                </button>
              </div>
            </div>

            {/* Content fields - always visible */}
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
                    onChange={(e) => onTitleChange(e.target.value)}
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
                    onChange={(e) => onUrlChange(e.target.value)}
                  />
                </div>
              </>
            )}

            {nodeType && (
              <div className="node-creation-field">
                <label className="node-creation-label">
                  {nodeType === 'source' ? 'Description' : 'Claim'}
                </label>
                <textarea
                  className="node-creation-textarea"
                  placeholder={nodeType === 'source' ? 'Describe the evidence...' : 'State the claim...'}
                  value={content}
                  onChange={(e) => onContentChange(e.target.value)}
                />
              </div>
            )}

            {/* Error display */}
            {error && (
              <div className="node-creation-error">
                {error}
              </div>
            )}
          </div>

          {/* Action buttons - only show on first box */}
          {showControls && (
            <div className="node-creation-footer">
              <button className="node-creation-btn" onClick={onClose}>
                Cancel
              </button>
              <button
                className="node-creation-btn node-creation-btn-primary"
                disabled={!canSubmit}
                onClick={onSubmit}
              >
                {isSubmitting ? 'Creating...' : 'Create'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
});
