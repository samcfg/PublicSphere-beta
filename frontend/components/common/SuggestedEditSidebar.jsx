import { useState, useEffect } from 'react';
import { fetchEntitySuggestions } from '../../APInterface/api.js';
import { SuggestedEditItem } from './SuggestedEditItem.jsx';

/**
 * SuggestedEditSidebar - Displays all suggested edits for an entity
 *
 * @param {Object} props
 * @param {string} props.entityUuid - UUID of the entity
 * @param {string} props.entityType - 'claim' | 'source' | 'connection'
 * @param {Object} props.currentData - Current entity data for diff comparison
 */
export function SuggestedEditSidebar({ entityUuid, entityType, currentData }) {
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadSuggestions = async () => {
    setLoading(true);
    setError(null);

    const response = await fetchEntitySuggestions(entityUuid);

    if (response.error) {
      setError(response.error);
      setLoading(false);
      return;
    }

    setSuggestions(response.data || []);
    setLoading(false);
  };

  useEffect(() => {
    if (entityUuid) {
      loadSuggestions();
    }
  }, [entityUuid]);

  // Group suggestions by status
  const pending = suggestions.filter(s => s.status === 'pending');
  const accepted = suggestions.filter(s => s.status === 'accepted');
  const rejected = suggestions.filter(s => s.status === 'rejected');

  if (loading) {
    return (
      <div className="suggested-edits-sidebar">
        <div className="suggested-edits-header">
          <h3>Suggested Edits</h3>
        </div>
        <div className="suggested-edits-loading">Loading suggestions...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="suggested-edits-sidebar">
        <div className="suggested-edits-header">
          <h3>Suggested Edits</h3>
        </div>
        <div className="suggested-edits-error">Error: {error}</div>
      </div>
    );
  }

  if (suggestions.length === 0) {
    return (
      <div className="suggested-edits-sidebar">
        <div className="suggested-edits-header">
          <h3>Suggested Edits</h3>
        </div>
        <div className="suggested-edits-empty">No suggestions yet</div>
      </div>
    );
  }

  return (
    <div className="suggested-edits-sidebar">
      <div className="suggested-edits-header">
        <h3>Suggested Edits</h3>
        <div className="suggested-edits-counts">
          {pending.length > 0 && <span className="count-pending">{pending.length} pending</span>}
          {accepted.length > 0 && <span className="count-accepted">{accepted.length} accepted</span>}
          {rejected.length > 0 && <span className="count-rejected">{rejected.length} rejected</span>}
        </div>
      </div>

      <div className="suggested-edits-content">
        {/* Pending suggestions */}
        {pending.length > 0 && (
          <div className="suggested-edits-section">
            <h4 className="section-title">Pending Review</h4>
            {pending.map(suggestion => (
              <SuggestedEditItem
                key={suggestion.suggestion_id}
                suggestion={suggestion}
                currentData={currentData}
                onVoteChange={loadSuggestions}
              />
            ))}
          </div>
        )}

        {/* Accepted suggestions */}
        {accepted.length > 0 && (
          <div className="suggested-edits-section">
            <h4 className="section-title">Accepted</h4>
            {accepted.map(suggestion => (
              <SuggestedEditItem
                key={suggestion.suggestion_id}
                suggestion={suggestion}
                currentData={currentData}
                onVoteChange={loadSuggestions}
              />
            ))}
          </div>
        )}

        {/* Rejected suggestions */}
        {rejected.length > 0 && (
          <div className="suggested-edits-section">
            <h4 className="section-title">Rejected</h4>
            {rejected.map(suggestion => (
              <SuggestedEditItem
                key={suggestion.suggestion_id}
                suggestion={suggestion}
                currentData={currentData}
                onVoteChange={loadSuggestions}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
