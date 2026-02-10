import { useState, useEffect } from 'react';
import { useAuth } from '../../utilities/AuthContext.jsx';
import { fetchUserContributionsList, fetchUserSocialContributions, toggleAnonymity, toggleSocialAnonymity } from '../../APInterface/api.js';
import { formatSourceType } from '../../utilities/formatters.js';

/**
 * UserContributions component
 * Displays user's claims, sources, connections, comments, ratings with anonymity toggles
 */
export function UserContributions() {
  const { token } = useAuth();
  const [contributions, setContributions] = useState(null);
  const [socialContributions, setSocialContributions] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('claims');

  useEffect(() => {
    loadContributions();
  }, [token]);

  const loadContributions = async () => {
    if (!token) {
      setError('Authentication required');
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    const [graphResponse, socialResponse] = await Promise.all([
      fetchUserContributionsList(token),
      fetchUserSocialContributions(token)
    ]);

    if (graphResponse.error) {
      setError(graphResponse.error);
      setLoading(false);
      return;
    }

    if (socialResponse.error) {
      setError(socialResponse.error);
      setLoading(false);
      return;
    }

    setContributions(graphResponse.data);
    setSocialContributions(socialResponse.data);
    setLoading(false);
  };

  const handleToggleAnonymity = async (entityId, entityType) => {
    if (!token) return;

    let response;

    // Use different endpoints for social vs graph entities
    if (entityType === 'comment' || entityType === 'rating') {
      // Social entities use integer IDs
      response = await toggleSocialAnonymity(token, {
        entity_id: entityId,
        entity_type: entityType,
      });
    } else {
      // Graph entities (claim, source, connection) use UUIDs
      response = await toggleAnonymity(token, {
        entity_uuid: entityId,
        entity_type: entityType,
        version_number: null,
      });
    }

    if (!response.error) {
      loadContributions();
    } else {
      console.error('Toggle anonymity failed:', response.error);
    }
  };

  if (loading) {
    return (
      <div className="user-contributions">
        <h2>My Contributions</h2>
        <p className="loading">Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="user-contributions">
        <h2>My Contributions</h2>
        <p className="error">Error: {error}</p>
      </div>
    );
  }

  if (!contributions || !socialContributions) {
    return (
      <div className="user-contributions">
        <h2>My Contributions</h2>
        <p>No data available</p>
      </div>
    );
  }

  const { claims, sources, connections } = contributions;
  const { comments, ratings } = socialContributions;

  return (
    <div className="user-contributions">
      <h2>My Contributions</h2>

      {/* Tabs */}
      <div className="contributions-tabs">
        <button
          onClick={() => setActiveTab('claims')}
          className={`contributions-tab ${activeTab === 'claims' ? 'active' : ''}`}
        >
          Claims ({claims.length})
        </button>
        <button
          onClick={() => setActiveTab('sources')}
          className={`contributions-tab ${activeTab === 'sources' ? 'active' : ''}`}
        >
          Sources ({sources.length})
        </button>
        <button
          onClick={() => setActiveTab('connections')}
          className={`contributions-tab ${activeTab === 'connections' ? 'active' : ''}`}
        >
          Connections ({connections.length})
        </button>
        <button
          onClick={() => setActiveTab('comments')}
          className={`contributions-tab ${activeTab === 'comments' ? 'active' : ''}`}
        >
          Comments ({comments.length})
        </button>
        <button
          onClick={() => setActiveTab('ratings')}
          className={`contributions-tab ${activeTab === 'ratings' ? 'active' : ''}`}
        >
          Ratings ({ratings.length})
        </button>
      </div>

      {/* Claims Table */}
      {activeTab === 'claims' && (
        <div className="contributions-table-wrapper">
          {claims.length === 0 ? (
            <p className="empty-message">No claims yet</p>
          ) : (
            <table className="contributions-table">
              <thead>
                <tr>
                  <th>Content</th>
                  <th>Created</th>
                  <th>Status</th>
                  <th>Anonymous</th>
                </tr>
              </thead>
              <tbody>
                {claims.map((claim) => (
                  <tr key={claim.uuid}>
                    <td>
                      <div className="table-content-cell" title={claim.content}>
                        {claim.content || '[No content]'}
                      </div>
                    </td>
                    <td style={{ whiteSpace: 'nowrap' }}>
                      {claim.created_at ? new Date(claim.created_at).toLocaleDateString() : 'N/A'}
                    </td>
                    <td>
                      <span className={`status-badge ${claim.is_anonymous ? 'anonymous' : 'public'}`}>
                        {claim.is_anonymous ? 'Anonymous' : 'Public'}
                      </span>
                    </td>
                    <td>
                      <label className="anon-checkbox-container">
                        <input
                          type="checkbox"
                          checked={claim.is_anonymous}
                          onChange={() => handleToggleAnonymity(claim.uuid, 'claim')}
                        />
                        <div className="anon-checkmark"></div>
                      </label>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Sources Table */}
      {activeTab === 'sources' && (
        <div className="contributions-table-wrapper">
          {sources.length === 0 ? (
            <p className="empty-message">No sources yet</p>
          ) : (
            <table className="contributions-table">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>URL</th>
                  <th>Type</th>
                  <th>Created</th>
                  <th>Status</th>
                  <th>Anonymous</th>
                </tr>
              </thead>
              <tbody>
                {sources.map((source) => (
                  <tr key={source.uuid}>
                    <td>
                      <div className="table-content-cell" title={source.title}>
                        {source.title || '[No title]'}
                      </div>
                    </td>
                    <td>
                      {source.url ? (
                        <a
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="table-url-link"
                          title={source.url}
                        >
                          {source.url}
                        </a>
                      ) : (
                        'N/A'
                      )}
                    </td>
                    <td>{source.source_type ? formatSourceType(source.source_type) : 'N/A'}</td>
                    <td style={{ whiteSpace: 'nowrap' }}>
                      {source.created_at ? new Date(source.created_at).toLocaleDateString() : 'N/A'}
                    </td>
                    <td>
                      <span className={`status-badge ${source.is_anonymous ? 'anonymous' : 'public'}`}>
                        {source.is_anonymous ? 'Anonymous' : 'Public'}
                      </span>
                    </td>
                    <td>
                      <label className="anon-checkbox-container">
                        <input
                          type="checkbox"
                          checked={source.is_anonymous}
                          onChange={() => handleToggleAnonymity(source.uuid, 'source')}
                        />
                        <div className="anon-checkmark"></div>
                      </label>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Connections Table */}
      {activeTab === 'connections' && (
        <div className="contributions-table-wrapper">
          {connections.length === 0 ? (
            <p className="empty-message">No connections yet</p>
          ) : (
            <table className="contributions-table">
              <thead>
                <tr>
                  <th>From</th>
                  <th>To</th>
                  <th>Logic</th>
                  <th>Notes</th>
                  <th>Created</th>
                  <th>Status</th>
                  <th>Anonymous</th>
                </tr>
              </thead>
              <tbody>
                {connections.map((conn) => (
                  <tr key={conn.uuid}>
                    <td>
                      <div className="table-node-type">{conn.source_node_type}</div>
                      <div className="table-node-display" title={conn.source_node_display}>
                        {conn.source_node_display}
                      </div>
                    </td>
                    <td>
                      <div className="table-node-type">{conn.target_node_type}</div>
                      <div className="table-node-display" title={conn.target_node_display}>
                        {conn.target_node_display}
                      </div>
                    </td>
                    <td>{conn.logic_type || 'N/A'}</td>
                    <td>
                      <div className="table-content-cell" title={conn.notes}>
                        {conn.notes || '—'}
                      </div>
                    </td>
                    <td style={{ whiteSpace: 'nowrap' }}>
                      {conn.created_at ? new Date(conn.created_at).toLocaleDateString() : 'N/A'}
                    </td>
                    <td>
                      <span className={`status-badge ${conn.is_anonymous ? 'anonymous' : 'public'}`}>
                        {conn.is_anonymous ? 'Anonymous' : 'Public'}
                      </span>
                    </td>
                    <td>
                      <label className="anon-checkbox-container">
                        <input
                          type="checkbox"
                          checked={conn.is_anonymous}
                          onChange={() => handleToggleAnonymity(conn.uuid, 'connection')}
                        />
                        <div className="anon-checkmark"></div>
                      </label>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Comments Table */}
      {activeTab === 'comments' && (
        <div className="contributions-table-wrapper">
          {comments.length === 0 ? (
            <p className="empty-message">No comments yet</p>
          ) : (
            <table className="contributions-table">
              <thead>
                <tr>
                  <th>Content</th>
                  <th>Entity Type</th>
                  <th>Entity UUID</th>
                  <th>Created</th>
                  <th>Status</th>
                  <th>Anonymous</th>
                </tr>
              </thead>
              <tbody>
                {comments.map((comment) => (
                  <tr key={comment.id}>
                    <td>
                      <div className="table-content-cell" title={comment.content}>
                        {comment.content || '[No content]'}
                      </div>
                    </td>
                    <td>{comment.entity_type}</td>
                    <td>
                      <div className="table-content-cell" title={comment.entity_uuid}>
                        {comment.entity_uuid.substring(0, 8)}...
                      </div>
                    </td>
                    <td style={{ whiteSpace: 'nowrap' }}>
                      {comment.created_at ? new Date(comment.created_at).toLocaleDateString() : 'N/A'}
                    </td>
                    <td>
                      <span className={`status-badge ${comment.is_anonymous ? 'anonymous' : 'public'}`}>
                        {comment.is_anonymous ? 'Anonymous' : 'Public'}
                      </span>
                    </td>
                    <td>
                      <label className="anon-checkbox-container">
                        <input
                          type="checkbox"
                          checked={comment.is_anonymous}
                          onChange={() => handleToggleAnonymity(comment.id, 'comment')}
                        />
                        <div className="anon-checkmark"></div>
                      </label>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Ratings Table */}
      {activeTab === 'ratings' && (
        <div className="contributions-table-wrapper">
          {ratings.length === 0 ? (
            <p className="empty-message">No ratings yet</p>
          ) : (
            <table className="contributions-table">
              <thead>
                <tr>
                  <th>Entity Type</th>
                  <th>Entity UUID</th>
                  <th>Dimension</th>
                  <th>Score</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {ratings.map((rating) => (
                  <tr key={rating.id}>
                    <td>{rating.entity_type}</td>
                    <td>
                      <div className="table-content-cell" title={rating.entity_uuid}>
                        {rating.entity_uuid.substring(0, 8)}...
                      </div>
                    </td>
                    <td>{rating.dimension || 'N/A'}</td>
                    <td>{rating.score}</td>
                    <td style={{ whiteSpace: 'nowrap' }}>
                      {rating.created_at ? new Date(rating.created_at).toLocaleDateString() : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
