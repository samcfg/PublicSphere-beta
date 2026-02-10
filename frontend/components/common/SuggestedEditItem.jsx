import { useState, useEffect } from 'react';
import { rateEntity, fetchEntityRatings } from '../../APInterface/api.js';
import { useAuth } from '../../utilities/AuthContext.jsx';

/**
 * Field name labels (mirrors labels used in SourceForm.jsx and getSourceMetadataFields)
 */
const FIELD_LABELS = {
  'content': 'Content',
  'title': 'Title',
  'url': 'URL',
  'source_type': 'Source Type',
  'authors': 'Authors',
  'editors': 'Editors',
  'doi': 'DOI',
  'publication_date': 'Publication Date',
  'container_title': 'Container Title',
  'publisher': 'Publisher',
  'publisher_location': 'Publisher Location',
  'volume': 'Volume',
  'issue': 'Issue',
  'pages': 'Pages',
  'edition': 'Edition',
  'isbn': 'ISBN',
  'issn': 'ISSN',
  'arxiv_id': 'arXiv ID',
  'accessed_date': 'Accessed Date',
  'notes': 'Notes',
  'excerpt': 'Excerpt',
  'jurisdiction': 'Jurisdiction',
  'legal_category': 'Legal Category',
  'court': 'Court',
  'decision_date': 'Decision Date',
  'case_name': 'Case Name',
  'code': 'Code',
  'section': 'Section'
};

/**
 * Format field name to human-readable label
 */
function formatFieldName(fieldName) {
  return FIELD_LABELS[fieldName] || fieldName.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

/**
 * Format timestamp as relative time (e.g., "2h ago", "3d ago")
 */
function formatRelativeTime(timestamp) {
  const now = new Date();
  const date = new Date(timestamp);
  const seconds = Math.floor((now - date) / 1000);

  if (seconds < 60) return 'just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
  return date.toLocaleDateString();
}

/**
 * DiffField - Shows a single field change in side-by-side format
 */
function DiffField({ fieldName, currentValue, proposedValue }) {
  return (
    <div className="diff-field">
      <div className="diff-field-label">{formatFieldName(fieldName)}</div>
      <div className="diff-field-content">
        <div className="diff-current">
          <span className="diff-label">Current:</span>
          <div className="diff-value">{currentValue || <em>(empty)</em>}</div>
        </div>
        <div className="diff-arrow">→</div>
        <div className="diff-proposed">
          <span className="diff-label">Proposed:</span>
          <div className="diff-value">{proposedValue || <em>(empty)</em>}</div>
        </div>
      </div>
    </div>
  );
}

/**
 * SuggestedEditItem - Displays a single suggested edit with voting
 *
 * @param {Object} props
 * @param {Object} props.suggestion - Suggestion object from API
 * @param {Object} props.currentData - Current entity data for comparison
 * @param {Function} props.onVoteChange - Callback when vote changes
 */
export function SuggestedEditItem({ suggestion, currentData, onVoteChange }) {
  const { user, token } = useAuth();
  const [userVote, setUserVote] = useState(null);
  const [isExpanded, setIsExpanded] = useState(true);

  // Fetch user's existing vote on mount
  useEffect(() => {
    const loadUserVote = async () => {
      if (!token) return;

      const response = await fetchEntityRatings(String(suggestion.suggestion_id), null, token);
      if (!response.error && response.data?.user_score != null) {
        setUserVote(response.data.user_score);
      }
    };

    loadUserVote();
  }, [suggestion.suggestion_id, token]);

  const handleVote = async (score) => {
    if (!token) return;

    // Rate the suggestion (entity_type='suggested_edit')
    await rateEntity(token, {
      entity_uuid: String(suggestion.suggestion_id),
      entity_type: 'suggested_edit',
      score: score
    });
    setUserVote(score);
    if (onVoteChange) onVoteChange();
  };

  // Get status badge styling
  const getStatusStyle = (status) => {
    switch (status) {
      case 'accepted':
        return { backgroundColor: '#10b981', color: 'white' };
      case 'rejected':
        return { backgroundColor: '#ef4444', color: 'white' };
      case 'pending':
      default:
        return { backgroundColor: '#d97706', color: 'white' };
    }
  };

  return (
    <div className="suggested-edit-item">
      <div className="suggested-edit-header">
        <div className="suggested-edit-meta">
          <span className="suggested-edit-author">
            {suggestion.suggested_by_username}
          </span>
          <span className="suggested-edit-dot">·</span>
          <span className="suggested-edit-timestamp">
            {formatRelativeTime(suggestion.created_at)}
          </span>
          <span
            className="suggested-edit-status-badge"
            style={getStatusStyle(suggestion.status)}
          >
            {suggestion.status}
          </span>
        </div>
        <button
          className="suggested-edit-collapse-btn"
          onClick={() => setIsExpanded(!isExpanded)}
          title={isExpanded ? 'Collapse' : 'Expand'}
        >
          {isExpanded ? '[-]' : '[+]'}
        </button>
      </div>

      {isExpanded && (
        <>
          {/* Changed fields */}
          <div className="suggested-edit-diffs">
            {Object.entries(suggestion.proposed_changes).map(([field, proposedValue]) => (
              <DiffField
                key={field}
                fieldName={field}
                currentValue={currentData?.[field]}
                proposedValue={proposedValue}
              />
            ))}
          </div>

          {/* Rationale */}
          <div className="suggested-edit-rationale">
            <div className="suggested-edit-rationale-label">Rationale:</div>
            <div className="suggested-edit-rationale-text">{suggestion.rationale}</div>
          </div>

          {/* Voting section */}
          <div className="suggested-edit-voting">
            <button
              className={`vote-btn upvote ${userVote === 100 ? 'active' : ''}`}
              onClick={() => handleVote(100)}
              disabled={!user || suggestion.status !== 'pending'}
              title={!user ? 'Log in to vote' : suggestion.status !== 'pending' ? 'Voting closed' : 'Upvote'}
            >
              ▲
            </button>
            <span className="vote-count">
              {suggestion.rating_stats?.count || 0}
              {suggestion.rating_stats?.avg != null && ` (${suggestion.rating_stats.avg}%)`}
            </span>
            <button
              className={`vote-btn downvote ${userVote === 0 ? 'active' : ''}`}
              onClick={() => handleVote(0)}
              disabled={!user || suggestion.status !== 'pending'}
              title={!user ? 'Log in to vote' : suggestion.status !== 'pending' ? 'Voting closed' : 'Downvote'}
            >
              ▼
            </button>
          </div>
        </>
      )}
    </div>
  );
}
