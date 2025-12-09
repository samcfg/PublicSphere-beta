import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { FaSearch } from 'react-icons/fa';
import { searchNodes } from '../../APInterface/api.js';

/**
 * SearchBar - Collapsible search with live results dropdown
 * Expands from icon to input field, shows compact node results
 */
export function SearchBar() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [query, setQuery] = useState('');
  const [nodeTypeFilter, setNodeTypeFilter] = useState(null); // null = both, 'claim', 'source'
  const [results, setResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);

  const searchRef = useRef(null);
  const inputRef = useRef(null);
  const debounceTimer = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setShowDropdown(false);
        if (!query) {
          setIsExpanded(false);
        }
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [query]);

  // Search with debounce
  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setShowDropdown(false);
      return;
    }

    // Clear previous timer
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    // Set new timer
    debounceTimer.current = setTimeout(async () => {
      setIsSearching(true);
      try {
        const response = await searchNodes(query, nodeTypeFilter);
        if (response.error) {
          console.error('Search error:', response.error);
          setResults([]);
        } else {
          console.log('Search results:', response.data?.results);
          setResults(response.data?.results || []);
          setShowDropdown(true);
        }
      } catch (error) {
        console.error('Search failed:', error);
        setResults([]);
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, [query, nodeTypeFilter]);

  const handleExpand = () => {
    setIsExpanded(true);
    setTimeout(() => inputRef.current?.focus(), 100);
  };

  const handleResultClick = () => {
    setShowDropdown(false);
    setQuery('');
    setIsExpanded(false);
  };

  const toggleFilter = (type) => {
    if (nodeTypeFilter === type) {
      setNodeTypeFilter(null); // Toggle off
    } else {
      setNodeTypeFilter(type);
    }
  };

  return (
    <div ref={searchRef} style={{
      position: 'relative',
      display: 'flex',
      alignItems: 'center',
      gap: '0.5rem'
    }}>
      {/* Search Icon / Input Container */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        backgroundColor: 'var(--bg-secondary)',
        border: '1px solid var(--accent-blue)',
        borderRadius: '24px',
        padding: '0.5rem 1rem',
        transition: 'all 0.3s ease',
        width: isExpanded ? '400px' : '48px',
        height: '48px',
        cursor: isExpanded ? 'text' : 'pointer'
      }}
      onClick={!isExpanded ? handleExpand : undefined}>
        <FaSearch style={{
          color: 'var(--accent-blue)',
          fontSize: '1.2rem',
          flexShrink: 0
        }} />

        {isExpanded && (
          <>
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search nodes..."
              style={{
                flex: 1,
                border: 'none',
                outline: 'none',
                backgroundColor: 'transparent',
                color: 'var(--text-primary)',
                fontSize: '1rem',
                marginLeft: '0.75rem',
                fontFamily: 'var(--font-family-base)'
              }}
            />

            {/* Filter Toggle Buttons */}
            <div style={{
              display: 'flex',
              gap: '0.25rem',
              marginLeft: '0.5rem'
            }}>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  toggleFilter('claim');
                }}
                style={{
                  padding: '0.25rem 0.75rem',
                  borderRadius: '12px',
                  border: 'none',
                  backgroundColor: nodeTypeFilter === 'claim' ? 'var(--accent-blue)' : 'var(--bg-primary)',
                  color: nodeTypeFilter === 'claim' ? 'var(--bg-secondary)' : 'var(--text-secondary)',
                  fontSize: '0.75rem',
                  fontWeight: nodeTypeFilter === 'claim' ? 'bold' : 'normal',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px'
                }}
              >
                Claim
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  toggleFilter('source');
                }}
                style={{
                  padding: '0.25rem 0.75rem',
                  borderRadius: '12px',
                  border: 'none',
                  backgroundColor: nodeTypeFilter === 'source' ? 'var(--accent-blue)' : 'var(--bg-primary)',
                  color: nodeTypeFilter === 'source' ? 'var(--bg-secondary)' : 'var(--text-secondary)',
                  fontSize: '0.75rem',
                  fontWeight: nodeTypeFilter === 'source' ? 'bold' : 'normal',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px'
                }}
              >
                Source
              </button>
            </div>
          </>
        )}
      </div>

      {/* Results Dropdown */}
      {isExpanded && showDropdown && (
        <div style={{
          position: 'absolute',
          top: 'calc(100% + 0.5rem)',
          left: 0,
          right: 0,
          backgroundColor: 'var(--bg-secondary)',
          border: '1px solid var(--accent-blue)',
          borderRadius: '8px',
          maxHeight: '400px',
          overflowY: 'auto',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
          zIndex: 1000
        }}>
          {isSearching && (
            <div style={{
              padding: '1rem',
              textAlign: 'center',
              color: 'var(--text-secondary)',
              fontSize: '0.9rem'
            }}>
              Searching...
            </div>
          )}

          {!isSearching && results.length === 0 && query.trim() && (
            <div style={{
              padding: '1rem',
              textAlign: 'center',
              color: 'var(--text-secondary)',
              fontSize: '0.9rem'
            }}>
              No results found for "{query}"
            </div>
          )}

          {!isSearching && results.length > 0 && (
            <div>
              {results.map((node) => (
                <Link
                  key={node.id}
                  to={`/context?id=${node.id}`}
                  onClick={handleResultClick}
                  style={{
                    display: 'block',
                    padding: '0.75rem 1rem',
                    borderBottom: '1px solid var(--bg-primary)',
                    textDecoration: 'none',
                    color: 'inherit',
                    transition: 'background-color 0.2s ease'
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
                    gap: '0.75rem'
                  }}>
                    {/* Node Type Badge */}
                    <span style={{
                      padding: '0.25rem 0.5rem',
                      borderRadius: '4px',
                      backgroundColor: node.node_type === 'claim' ? 'var(--accent-blue)' : 'var(--accent-green)',
                      color: 'var(--bg-secondary)',
                      fontSize: '0.7rem',
                      fontWeight: 'bold',
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px',
                      flexShrink: 0
                    }}>
                      {node.node_type}
                    </span>

                    {/* Node Content (truncated) */}
                    <span style={{
                      flex: 1,
                      fontSize: '0.9rem',
                      color: 'var(--text-primary)',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      {node.node_type === 'source' ? (node.title || node.content) : node.content}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
