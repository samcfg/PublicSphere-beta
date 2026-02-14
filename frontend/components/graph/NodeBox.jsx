import { forwardRef, useState, useEffect, useImperativeHandle, useRef } from 'react';
import { searchNodes } from '../../APInterface/api.js';
import { NodeDisplay } from '../common/NodeDisplay.jsx';
import { ClaimForm } from './ClaimForm.jsx';
import { SourceForm } from './SourceForm.jsx';
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
 * @param {string} props.mode - 'create' | 'edit' (default: 'create')
 * @param {Object} props.initialData - Pre-fill data for edit mode: {nodeType, content, title?, url?}
 * @param {number} props.index - Index of this node box (for compound connections)
 * @param {Function} props.onValidationChange - Callback: (index, isValid) => void
 * @param {Function} props.onClose - Close/cancel callback
 * @param {Function} props.onSubmit - Submit/create callback (called by button)
 * @param {boolean} props.isSubmitting - Whether parent is currently submitting
 * @param {boolean} props.showControls - Whether to show close/submit buttons
 * @param {React.Ref} ref - Forwarded ref exposing imperative methods
 */
export const NodeBox = forwardRef(({
  mode = 'create',
  initialData = null,
  index = 0,
  onValidationChange,
  onNodeTypeChange,
  onClose,
  onSubmit,
  isSubmitting = false,
  showControls = true
}, ref) => {
  // Input mode: 'input' (creating new) or 'selected' (using existing)
  const [inputMode, setInputMode] = useState('input');

  // Internal state - each box is independent
  const [nodeType, setNodeType] = useState(null); // 'claim' or 'source'
  const [content, setContent] = useState('');
  const [title, setTitle] = useState(''); // For sources - required
  const [url, setUrl] = useState('');
  const [error, setError] = useState(null);

  // Source metadata fields
  const [source_type, setSourceType] = useState('');
  const [authors, setAuthors] = useState([]);
  const [doi, setDoi] = useState('');
  const [publication_date, setPublicationDate] = useState('');
  const [container_title, setContainerTitle] = useState('');
  const [publisher, setPublisher] = useState('');
  const [volume, setVolume] = useState('');
  const [issue, setIssue] = useState('');
  const [pages, setPages] = useState('');
  const [edition, setEdition] = useState('');
  const [isbn, setIsbn] = useState('');
  const [issn, setIssn] = useState('');
  const [arxiv_id, setArxivId] = useState('');

  // Selected existing node (when mode === 'selected')
  const [selectedNode, setSelectedNode] = useState(null); // {id, node_type, content, title?, url?}

  // Search state
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const debounceTimer = useRef(null);

  // Validation logic
  const isValid = (() => {
    if (inputMode === 'selected') {
      return selectedNode !== null;
    }
    // Input mode - coerce to boolean to avoid string/truthy confusion
    // Sources require: title + source_type (content is optional description)
    // Claims require: content only
    if (nodeType === 'source') {
      return !!(title.trim() && source_type.trim());
    }
    return !!(nodeType && content.trim());
  })();

  // Notify parent whenever validation state changes
  useEffect(() => {
    if (onValidationChange) {
      onValidationChange(index, isValid);
    }
  }, [index, isValid, onValidationChange]);

  // Notify parent whenever node type changes
  useEffect(() => {
    if (onNodeTypeChange) {
      onNodeTypeChange(nodeType);
    }
  }, [nodeType, onNodeTypeChange]);

  // Internal DOM ref for height measurement
  const domRef = useRef(null);

  // Pre-populate fields in edit mode
  useEffect(() => {
    if (mode === 'edit' && initialData) {
      setNodeType(initialData.nodeType);
      setContent(initialData.content || '');
      setTitle(initialData.title || '');
      setUrl(initialData.url || '');
      setSourceType(initialData.source_type || '');
      setAuthors(initialData.authors || []);
      setDoi(initialData.doi || '');
      setPublicationDate(initialData.publication_date || '');
      setContainerTitle(initialData.container_title || '');
      setPublisher(initialData.publisher || '');
      setVolume(initialData.volume || '');
      setIssue(initialData.issue || '');
      setPages(initialData.pages || '');
      setEdition(initialData.edition || '');
      setIsbn(initialData.isbn || '');
      setIssn(initialData.issn || '');
      setArxivId(initialData.arxiv_id || '');
      // Stay in 'input' mode for editing (not 'selected')
    }
  }, [mode, initialData]);

  // Expose imperative methods to parent via ref
  useImperativeHandle(ref, () => ({
    /**
     * Get current data - either new node data or selected existing node
     * @returns {Object} {inputMode: 'input'|'selected', nodeType, content, title, url, metadata..., selectedNodeId?}
     */
    getData: () => {
      if (inputMode === 'selected') {
        return {
          inputMode: 'selected',
          selectedNodeId: selectedNode.id,
          nodeType: selectedNode.node_type,
          content: selectedNode.content,
          title: selectedNode.title || '',
          url: selectedNode.url || ''
        };
      }

      const data = {
        inputMode: 'input',
        nodeType,
        content: content.trim(),
        title: title.trim(),
        url: url.trim()
      };

      // Include source metadata if it's a source
      if (nodeType === 'source') {
        data.source_type = source_type.trim();
        if (authors.length > 0) data.authors = authors;
        if (doi.trim()) data.doi = doi.trim();
        if (publication_date.trim()) data.publication_date = publication_date.trim();
        if (container_title.trim()) data.container_title = container_title.trim();
        if (publisher.trim()) data.publisher = publisher.trim();
        if (volume.trim()) data.volume = volume.trim();
        if (issue.trim()) data.issue = issue.trim();
        if (pages.trim()) data.pages = pages.trim();
        if (edition.trim()) data.edition = edition.trim();
        if (isbn.trim()) data.isbn = isbn.trim();
        if (issn.trim()) data.issn = issn.trim();
        if (arxiv_id.trim()) data.arxiv_id = arxiv_id.trim();
      }

      return data;
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
      setInputMode('input');
      setNodeType(null);
      setContent('');
      setTitle('');
      setUrl('');
      setError(null);
      setSelectedNode(null);
      setSearchResults([]);
      setShowResults(false);
      // Reset source metadata
      setSourceType('');
      setAuthors([]);
      setDoi('');
      setPublicationDate('');
      setContainerTitle('');
      setPublisher('');
      setVolume('');
      setIssue('');
      setPages('');
      setEdition('');
      setIsbn('');
      setIssn('');
      setArxivId('');
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
    if (inputMode !== 'input' || !nodeType) return;

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
  }, [content, nodeType, inputMode]);

  // Debounced search on title/URL change (for sources)
  useEffect(() => {
    if (inputMode !== 'input' || nodeType !== 'source') return;

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
  }, [title, url, nodeType, inputMode, content]);

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
    setInputMode('selected');
    setShowResults(false);
    setError(null);
  };

  const handleUnselectNode = () => {
    setSelectedNode(null);
    setInputMode('input');
  };

  // Handle metadata fetched from CitationFetcher
  const handleMetadataFetched = (metadata) => {
    // Auto-populate form fields from fetched metadata (only if empty)
    if (metadata.title && !title) {
      setTitle(metadata.title);
    }
    if (metadata.source_type && !source_type) {
      setSourceType(metadata.source_type);
    }
    if (metadata.authors && Array.isArray(metadata.authors) && authors.length === 0) {
      setAuthors(metadata.authors);
    }
    if (metadata.doi && !doi) {
      setDoi(metadata.doi);
    }
    if (metadata.publication_date && !publication_date) {
      setPublicationDate(metadata.publication_date);
    }
    if (metadata.container_title && !container_title) {
      setContainerTitle(metadata.container_title);
    }
    if (metadata.publisher && !publisher) {
      setPublisher(metadata.publisher);
    }
    if (metadata.volume && !volume) {
      setVolume(metadata.volume);
    }
    if (metadata.issue && !issue) {
      setIssue(metadata.issue);
    }
    if (metadata.pages && !pages) {
      setPages(metadata.pages);
    }
    if (metadata.isbn && !isbn) {
      setIsbn(metadata.isbn);
    }
    if (metadata.issn && !issn) {
      setIssn(metadata.issn);
    }
    if (metadata.arxiv_id && !arxiv_id) {
      setArxivId(metadata.arxiv_id);
    }
  };

  // Determine highlight color based on node type
  const getHighlightColor = () => {
    const type = inputMode === 'selected' ? selectedNode?.node_type : nodeType;
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
              {mode === 'edit'
                ? `Edit ${nodeType === 'source' ? 'Evidence' : 'Claim'}`
                : (index > 0 ? `Node ${index + 1}` : 'New Node')}
            </h2>
            {showControls && (
              <button className="node-creation-close" onClick={onClose}>
                &times;
              </button>
            )}
          </div>

          <div className="node-creation-content">
            {/* SELECTED MODE: Show selected node with NodeDisplay */}
            {inputMode === 'selected' && selectedNode && (
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
            {inputMode === 'input' && (
              <>
                {/* Node type selection - only show in create mode */}
                {mode === 'create' && (
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
                )}

                {/* Form fields - delegated to type-specific components */}
                {nodeType === 'source' && (
                  <SourceForm
                    title={title}
                    url={url}
                    content={content}
                    source_type={source_type}
                    authors={authors}
                    doi={doi}
                    publication_date={publication_date}
                    container_title={container_title}
                    publisher={publisher}
                    volume={volume}
                    issue={issue}
                    pages={pages}
                    edition={edition}
                    isbn={isbn}
                    issn={issn}
                    arxiv_id={arxiv_id}
                    onTitleChange={handleTitleChange}
                    onUrlChange={handleUrlChange}
                    onContentChange={handleContentChange}
                    onSourceTypeChange={setSourceType}
                    onAuthorsChange={setAuthors}
                    onDoiChange={setDoi}
                    onPublicationDateChange={setPublicationDate}
                    onContainerTitleChange={setContainerTitle}
                    onPublisherChange={setPublisher}
                    onVolumeChange={setVolume}
                    onIssueChange={setIssue}
                    onPagesChange={setPages}
                    onEditionChange={setEdition}
                    onIsbnChange={setIsbn}
                    onIssnChange={setIssn}
                    onArxivIdChange={setArxivId}
                    onMetadataFetched={handleMetadataFetched}
                    error={error}
                  />
                )}

                {nodeType === 'claim' && (
                  <ClaimForm
                    content={content}
                    onContentChange={handleContentChange}
                    error={error}
                  />
                )}

                {/* Search results dropdown - shown for both types */}
                {nodeType && showResults && searchResults.length > 0 && (
                  <div style={{
                    backgroundColor: 'var(--bg-secondary)',
                    border: '1px solid var(--accent-blue)',
                    borderRadius: '4px',
                    maxHeight: '200px',
                    overflowY: 'auto',
                    boxShadow: '0 4px 8px rgba(0, 0, 0, 0.2)',
                    marginTop: '8px'
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
                {mode === 'edit'
                  ? (isSubmitting ? 'Saving...' : 'Save Changes')
                  : (isSubmitting ? 'Creating...' : 'Create')}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
});

NodeBox.displayName = 'NodeBox';
