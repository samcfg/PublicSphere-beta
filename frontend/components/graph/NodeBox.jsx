import { forwardRef, useState, useEffect, useImperativeHandle, useRef } from 'react';
import { searchNodes } from '../../APInterface/api.js';
import { NodeDisplay } from '../common/NodeDisplay.jsx';
import '../../styles/components/node-creation-panel.css';

/**
 * Self-contained node creation box with internal state management and live search
 *
 * Architecture:
 * - Manages its own form state (nodeType, content, title, url)
 * - Live search as user types (debounced)
 * - Two modes: 'input' (creating new) and 'selected' (using existing node)
 * - Validates internally and notifies parent of validation state changes
 * - Exposes imperative methods via ref for parent to orchestrate submission
 *
 * @param {Object} props
 * @param {number} props.index - Index of this node box (for compound connections)
 * @param {Function} props.onValidationChange - Callback: (index, isValid) => void
 * @param {Function} props.onClose - Close/cancel callback
 * @param {Function} props.onSubmit - Submit/create callback (called by button)
 * @param {boolean} props.isSubmitting - Whether parent is currently submitting
 * @param {boolean} props.showControls - Whether to show close/submit buttons
 * @param {React.Ref} ref - Forwarded ref exposing imperative methods
 */
export const NodeBox = forwardRef(({
  index = 0,
  onValidationChange,
  onClose,
  onSubmit,
  isSubmitting = false,
  showControls = true
}, ref) => {
  // Mode: 'input' (creating new) or 'selected' (using existing)
  const [mode, setMode] = useState('input');

  // Internal state - each box is independent
  const [nodeType, setNodeType] = useState(null); // 'claim' or 'source'
  const [content, setContent] = useState('');
  const [title, setTitle] = useState(''); // For sources - required
  const [url, setUrl] = useState('');
  const [error, setError] = useState(null);

  // Selected existing node (when mode === 'selected')
  const [selectedNode, setSelectedNode] = useState(null); // {id, node_type, content, title?, url?}

  // Search state
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const debounceTimer = useRef(null);

  // Validation logic
  const isValid = (() => {
    if (mode === 'selected') {
      return selectedNode !== null;
    }
    // Input mode
    return nodeType && content.trim() &&
      (nodeType !== 'source' || title.trim());
  })();

  // Notify parent whenever validation state changes
  useEffect(() => {
    if (onValidationChange) {
      onValidationChange(index, isValid);
    }
  }, [index, isValid, onValidationChange]);

  // Internal DOM ref for height measurement
  const domRef = useRef(null);

  // Expose imperative methods to parent via ref
  useImperativeHandle(ref, () => ({
    /**
     * Get current data - either new node data or selected existing node
     * @returns {Object} {mode: 'input'|'selected', nodeType, content, title, url, selectedNodeId?}
     */
    getData: () => {
      if (mode === 'selected') {
        return {
          mode: 'selected',
          selectedNodeId: selectedNode.id,
          nodeType: selectedNode.node_type,
          content: selectedNode.content,
          title: selectedNode.title || '',
          url: selectedNode.url || ''
        };
      }
      return {
        mode: 'input',
        nodeType,
        content: content.trim(),
        title: title.trim(),
        url: url.trim()
      };
    },

    /**
     * Check if current state is valid
     * @returns {boolean}
     */
    isValid: () => isValid,

    /**
     * Set error from external source (e.g., API duplicate detection)
     * @param {React.ReactNode} err - Error message or JSX element
     */
    setError: (err) => setError(err),

    /**
     * Reset all form state
     */
    reset: () => {
      setMode('input');
      setNodeType(null);
      setContent('');
      setTitle('');
      setUrl('');
      setError(null);
      setSelectedNode(null);
      setSearchResults([]);
      setShowResults(false);
    },

    /**
     * Get bounding client rect for positioning calculations
     * @returns {DOMRect}
     */
    getBoundingClientRect: () => domRef.current?.getBoundingClientRect()
  }));

  // Live search function
  const performSearch = async (query, searchNodeType) => {
    if (!query.trim() || query.length < 2) {
      setSearchResults([]);
      setShowResults(false);
      return;
    }

    setIsSearching(true);
    try {
      const response = await searchNodes(query, searchNodeType);
      if (response.error) {
        console.error('Search error:', response.error);
        setSearchResults([]);
      } else {
        const results = response.data?.results || [];
        setSearchResults(results);
        setShowResults(results.length > 0);
      }
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  // Debounced search on content change
  useEffect(() => {
    if (mode !== 'input' || !nodeType) return;

    // Clear previous timer
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    // Set new timer for content search
    if (content) {
      debounceTimer.current = setTimeout(() => {
        performSearch(content, nodeType);
      }, 300);
    } else {
      setSearchResults([]);
      setShowResults(false);
    }

    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, [content, nodeType, mode]);

  // Debounced search on title/URL change (for sources)
  useEffect(() => {
    if (mode !== 'input' || nodeType !== 'source') return;

    // Clear previous timer
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    // Search by title or URL (whichever is being typed)
    const searchQuery = title || url;
    if (searchQuery) {
      debounceTimer.current = setTimeout(() => {
        performSearch(searchQuery, 'source');
      }, 300);
    } else if (!content) {
      // Only clear if content is also empty
      setSearchResults([]);
      setShowResults(false);
    }

    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, [title, url, nodeType, mode, content]);

  // Internal handlers
  const handleNodeTypeChange = (type) => {
    setNodeType(type);
    setError(null);
    setSearchResults([]);
    setShowResults(false);
  };

  const handleContentChange = (value) => {
    setContent(value);
    setError(null);
  };

  const handleTitleChange = (value) => {
    setTitle(value);
    setError(null);
  };

  const handleUrlChange = (value) => {
    setUrl(value);
    setError(null);
  };

  const handleSelectNode = (node) => {
    setSelectedNode(node);
    setMode('selected');
    setShowResults(false);
    setError(null);
  };

  const handleUnselectNode = () => {
    setSelectedNode(null);
    setMode('input');
  };

  // Determine highlight color based on node type
  const getHighlightColor = () => {
    const type = mode === 'selected' ? selectedNode?.node_type : nodeType;
    if (!type) return 'var(--accent-blue)'; // Default neutral
    if (type === 'source') return 'var(--accent-green)';
    return 'var(--accent-blue)'; // claim
  };

  return (
    <div ref={domRef} className="node-creation-panel" onClick={(e) => e.stopPropagation()}>
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
            {/* SELECTED MODE: Show selected node with NodeDisplay */}
            {mode === 'selected' && selectedNode && (
              <div>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  marginBottom: '12px',
                  padding: '8px',
                  backgroundColor: 'var(--bg-primary)',
                  borderRadius: '4px'
                }}>
                  <span style={{
                    padding: '4px 8px',
                    borderRadius: '4px',
                    backgroundColor: getHighlightColor(),
                    color: 'var(--bg-secondary)',
                    fontSize: '0.75rem',
                    fontWeight: 'bold',
                    textTransform: 'uppercase'
                  }}>
                    Using Existing {selectedNode.node_type}
                  </span>
                  <button
                    onClick={handleUnselectNode}
                    style={{
                      marginLeft: 'auto',
                      padding: '4px 12px',
                      fontSize: '0.85rem',
                      backgroundColor: 'transparent',
                      border: '1px solid var(--text-secondary)',
                      borderRadius: '4px',
                      color: 'var(--text-secondary)',
                      cursor: 'pointer'
                    }}
                  >
                    Change
                  </button>
                </div>
                <div style={{
                  maxHeight: '300px',
                  overflow: 'auto',
                  border: '1px solid var(--attr-border)',
                  borderRadius: '4px'
                }}>
                  <NodeDisplay
                    nodeId={selectedNode.id}
                    nodeType={selectedNode.node_type}
                    content={selectedNode.node_type === 'claim' ? selectedNode.content : selectedNode.title}
                    url={selectedNode.url}
                    containerStyle={{
                      padding: '20px',
                      border: 'none'
                    }}
                    contentStyle={{
                      fontSize: '0.9rem',
                      maxWidth: '100%'
                    }}
                  />
                </div>
              </div>
            )}

            {/* INPUT MODE: Show form fields */}
            {mode === 'input' && (
              <>
                {/* Node type selection */}
                <div className="node-creation-field">
                  <label className="node-creation-label">What are you adding?</label>
                  <div className="node-creation-type-buttons">
                    <button
                      className={`node-creation-type-btn ${nodeType === 'source' ? 'selected' : ''}`}
                      onClick={() => handleNodeTypeChange('source')}
                      style={{
                        backgroundColor: nodeType === 'source' ? 'var(--accent-green)' : 'transparent',
                        borderColor: nodeType === 'source' ? 'var(--accent-green)' : 'var(--attr-border)'
                      }}
                    >
                      Evidence
                    </button>
                    <button
                      className={`node-creation-type-btn ${nodeType === 'claim' ? 'selected' : ''}`}
                      onClick={() => handleNodeTypeChange('claim')}
                      style={{
                        backgroundColor: nodeType === 'claim' ? 'var(--accent-blue)' : 'transparent',
                        borderColor: nodeType === 'claim' ? 'var(--accent-blue)' : 'var(--attr-border)'
                      }}
                    >
                      Claim
                    </button>
                  </div>
                </div>

                {/* Source-specific fields */}
                {nodeType === 'source' && (
                  <>
                    <div className="node-creation-field" style={{ position: 'relative' }}>
                      <label className="node-creation-label">
                        Title <span style={{ color: '#ff4444' }}>*</span>
                      </label>
                      <input
                        type="text"
                        className={`node-creation-input ${nodeType === 'source' && !title.trim() ? 'error' : ''}`}
                        placeholder="Source title (required)"
                        value={title}
                        onChange={(e) => handleTitleChange(e.target.value)}
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
                        onChange={(e) => handleUrlChange(e.target.value)}
                      />
                    </div>
                  </>
                )}

                {/* Content field - shown after type is selected */}
                {nodeType && (
                  <div className="node-creation-field" style={{ position: 'relative' }}>
                    <label className="node-creation-label">
                      {nodeType === 'source' ? 'Description' : 'Claim'}
                    </label>
                    <textarea
                      className="node-creation-textarea"
                      placeholder={nodeType === 'source' ? 'Describe the evidence...' : 'State the claim...'}
                      value={content}
                      onChange={(e) => handleContentChange(e.target.value)}
                    />

                    {/* Search results dropdown */}
                    {showResults && searchResults.length > 0 && (
                      <div style={{
                        position: 'absolute',
                        top: '100%',
                        left: 0,
                        right: 0,
                        backgroundColor: 'var(--bg-secondary)',
                        border: '1px solid var(--accent-blue)',
                        borderRadius: '4px',
                        maxHeight: '200px',
                        overflowY: 'auto',
                        boxShadow: '0 4px 8px rgba(0, 0, 0, 0.2)',
                        zIndex: 100,
                        marginTop: '4px'
                      }}>
                        <div style={{
                          padding: '8px 12px',
                          fontSize: '0.75rem',
                          color: 'var(--text-secondary)',
                          borderBottom: '1px solid var(--attr-border)',
                          backgroundColor: 'var(--bg-primary)'
                        }}>
                          {isSearching ? 'Searching...' : `${searchResults.length} similar ${nodeType}(s) found`}
                        </div>
                        {searchResults.map((result) => (
                          <div
                            key={result.id}
                            onClick={() => handleSelectNode(result)}
                            style={{
                              padding: '10px 12px',
                              borderBottom: '1px solid var(--bg-primary)',
                              cursor: 'pointer',
                              transition: 'background-color 0.2s'
                            }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.backgroundColor = 'var(--bg-primary)';
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.backgroundColor = 'transparent';
                            }}
                          >
                            <div style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: '8px',
                              marginBottom: '4px'
                            }}>
                              <span style={{
                                padding: '2px 6px',
                                borderRadius: '3px',
                                backgroundColor: result.node_type === 'claim' ? 'var(--accent-blue)' : 'var(--accent-green)',
                                color: 'var(--bg-secondary)',
                                fontSize: '0.65rem',
                                fontWeight: 'bold',
                                textTransform: 'uppercase'
                              }}>
                                {result.node_type}
                              </span>
                            </div>
                            <div style={{
                              fontSize: '0.85rem',
                              color: 'var(--text-primary)',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              display: '-webkit-box',
                              WebkitLineClamp: 2,
                              WebkitBoxOrient: 'vertical'
                            }}>
                              {result.node_type === 'source' ? result.title : result.content}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Error display */}
                {error && (
                  <div className="node-creation-error">
                    {error}
                  </div>
                )}
              </>
            )}
          </div>

          {/* Action buttons - only show if showControls is true */}
          {showControls && (
            <div className="node-creation-footer">
              <button className="node-creation-btn" onClick={onClose}>
                Cancel
              </button>
              <button
                className="node-creation-btn node-creation-btn-primary"
                disabled={!isValid || isSubmitting}
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

NodeBox.displayName = 'NodeBox';
