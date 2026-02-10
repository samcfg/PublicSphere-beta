import { useState, useEffect } from 'react';
import { useAuth } from '../../utilities/AuthContext.jsx';
import { fetchUserDataExport } from '../../APInterface/api.js';
import { formatSourceType, formatAuthors } from '../../utilities/formatters.js';

/**
 * UserData component - GDPR data export
 * Displays all user data in 5 compact tables:
 * 1. User Account Info
 * 2. User Profile
 * 3. Creation Attributions
 * 4. Modification Attributions
 * 5. All Contributions (claims, sources, connections, comments, ratings)
 */
export function UserData() {
  const { token } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, [token]);

  const loadData = async () => {
    if (!token) {
      setError('Authentication required');
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    const response = await fetchUserDataExport(token);

    if (response.error) {
      setError(response.error);
      setLoading(false);
      return;
    }

    setData(response.data);
    setLoading(false);
  };

  if (loading) {
    return (
      <div className="user-data">
        <h2>My Data</h2>
        <p className="loading">Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="user-data">
        <h2>My Data</h2>
        <p className="error">Error: {error}</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="user-data">
        <h2>My Data</h2>
        <p>No data available</p>
      </div>
    );
  }

  const { user, profile, attributions, modifications, contributions } = data;
  const { claims, sources, connections, comments, ratings } = contributions;

  return (
    <div className="user-data">
      <h2>My Data</h2>
      <p className="data-description">Complete export of your account data (GDPR compliant)</p>

      {/* 1. User Account Info */}
      <section className="data-section">
        <h3>Account Information</h3>
        <table className="data-table compact">
          <thead>
            <tr>
              <th>Field</th>
              <th>Value</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>ID</td>
              <td>{user.id}</td>
            </tr>
            <tr>
              <td>Username</td>
              <td>{user.username}</td>
            </tr>
            <tr>
              <td>Email</td>
              <td>{user.email || 'Not provided'}</td>
            </tr>
            <tr>
              <td>First Name</td>
              <td>{user.first_name || 'Not provided'}</td>
            </tr>
            <tr>
              <td>Last Name</td>
              <td>{user.last_name || 'Not provided'}</td>
            </tr>
            <tr>
              <td>Account Active</td>
              <td>{user.is_active ? 'Yes' : 'No'}</td>
            </tr>
            <tr>
              <td>Staff Status</td>
              <td>{user.is_staff ? 'Yes' : 'No'}</td>
            </tr>
            <tr>
              <td>Superuser</td>
              <td>{user.is_superuser ? 'Yes' : 'No'}</td>
            </tr>
            <tr>
              <td>Date Joined</td>
              <td>{new Date(user.date_joined).toLocaleString()}</td>
            </tr>
            <tr>
              <td>Last Login</td>
              <td>{user.last_login ? new Date(user.last_login).toLocaleString() : 'Never'}</td>
            </tr>
          </tbody>
        </table>
      </section>

      {/* 2. User Profile */}
      <section className="data-section">
        <h3>Profile</h3>
        <table className="data-table compact">
          <thead>
            <tr>
              <th>Field</th>
              <th>Value</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Display Name</td>
              <td>{profile.display_name || 'Not set'}</td>
            </tr>
            <tr>
              <td>Bio</td>
              <td>{profile.bio || 'Not set'}</td>
            </tr>
            <tr>
              <td>Total Claims</td>
              <td>{profile.total_claims}</td>
            </tr>
            <tr>
              <td>Total Sources</td>
              <td>{profile.total_sources}</td>
            </tr>
            <tr>
              <td>Total Connections</td>
              <td>{profile.total_connections}</td>
            </tr>
            <tr>
              <td>Reputation Score</td>
              <td>{profile.reputation_score}</td>
            </tr>
            <tr>
              <td>Profile Last Updated</td>
              <td>{new Date(profile.last_updated).toLocaleString()}</td>
            </tr>
          </tbody>
        </table>
      </section>

      {/* 3. Creation Attributions */}
      <section className="data-section">
        <h3>Creation Attributions ({attributions.length})</h3>
        {attributions.length === 0 ? (
          <p className="empty-message">No creation attributions</p>
        ) : (
          <table className="data-table compact">
            <thead>
              <tr>
                <th>Entity UUID</th>
                <th>Type</th>
                <th>Anonymous</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {attributions.map((attr, idx) => (
                <tr key={idx}>
                  <td className="uuid-cell">{attr.entity_uuid}</td>
                  <td>{attr.entity_type}</td>
                  <td>{attr.is_anonymous ? 'Yes' : 'No'}</td>
                  <td>{new Date(attr.timestamp).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {/* 4. Modification Attributions */}
      <section className="data-section">
        <h3>Modification Attributions ({modifications.length})</h3>
        {modifications.length === 0 ? (
          <p className="empty-message">No modification attributions</p>
        ) : (
          <table className="data-table compact">
            <thead>
              <tr>
                <th>Entity UUID</th>
                <th>Type</th>
                <th>Version</th>
                <th>Anonymous</th>
                <th>Modified</th>
              </tr>
            </thead>
            <tbody>
              {modifications.map((mod, idx) => (
                <tr key={idx}>
                  <td className="uuid-cell">{mod.entity_uuid}</td>
                  <td>{mod.entity_type}</td>
                  <td>v{mod.version_number}</td>
                  <td>{mod.is_anonymous ? 'Yes' : 'No'}</td>
                  <td>{new Date(mod.timestamp).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {/* 5. All Contributions */}
      <section className="data-section">
        <h3>All Contributions</h3>

        <h4>Claims ({claims.length})</h4>
        {claims.length === 0 ? (
          <p className="empty-message">No claims</p>
        ) : (
          <table className="data-table compact">
            <thead>
              <tr>
                <th>UUID</th>
                <th>Content</th>
                <th>Created</th>
                <th>Anonymous</th>
              </tr>
            </thead>
            <tbody>
              {claims.map((claim) => (
                <tr key={claim.uuid}>
                  <td className="uuid-cell">{claim.uuid.substring(0, 8)}...</td>
                  <td className="content-cell">{claim.content || '[No content]'}</td>
                  <td>{new Date(claim.created_at).toLocaleDateString()}</td>
                  <td>{claim.is_anonymous ? 'Yes' : 'No'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        <h4>Sources ({sources.length})</h4>
        {sources.length === 0 ? (
          <p className="empty-message">No sources</p>
        ) : (
          <table className="data-table compact">
            <thead>
              <tr>
                <th>UUID</th>
                <th>Title</th>
                <th>Type</th>
                <th>Authors</th>
                <th>URL</th>
                <th>DOI</th>
                <th>Publication Date</th>
                <th>Created</th>
                <th>Anonymous</th>
              </tr>
            </thead>
            <tbody>
              {sources.map((source) => (
                <tr key={source.uuid}>
                  <td className="uuid-cell">{source.uuid.substring(0, 8)}...</td>
                  <td className="content-cell">{source.title || '[No title]'}</td>
                  <td>{source.source_type ? formatSourceType(source.source_type) : 'N/A'}</td>
                  <td className="content-cell">{formatAuthors(source.authors) || 'N/A'}</td>
                  <td className="content-cell">
                    {source.url ? (
                      <a href={source.url} target="_blank" rel="noopener noreferrer">
                        {source.url}
                      </a>
                    ) : (
                      'N/A'
                    )}
                  </td>
                  <td className="content-cell">{source.doi || 'N/A'}</td>
                  <td>{source.publication_date || 'N/A'}</td>
                  <td>{new Date(source.created_at).toLocaleDateString()}</td>
                  <td>{source.is_anonymous ? 'Yes' : 'No'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        <h4>Connections ({connections.length})</h4>
        {connections.length === 0 ? (
          <p className="empty-message">No connections</p>
        ) : (
          <table className="data-table compact">
            <thead>
              <tr>
                <th>UUID</th>
                <th>From</th>
                <th>To</th>
                <th>Logic</th>
                <th>Created</th>
                <th>Anonymous</th>
              </tr>
            </thead>
            <tbody>
              {connections.map((conn) => (
                <tr key={conn.uuid}>
                  <td className="uuid-cell">{conn.uuid.substring(0, 8)}...</td>
                  <td className="content-cell">{conn.source_node_display}</td>
                  <td className="content-cell">{conn.target_node_display}</td>
                  <td>{conn.logic_type}</td>
                  <td>{new Date(conn.created_at).toLocaleDateString()}</td>
                  <td>{conn.is_anonymous ? 'Yes' : 'No'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        <h4>Comments ({comments.length})</h4>
        {comments.length === 0 ? (
          <p className="empty-message">No comments</p>
        ) : (
          <table className="data-table compact">
            <thead>
              <tr>
                <th>ID</th>
                <th>Content</th>
                <th>Entity Type</th>
                <th>Entity UUID</th>
                <th>Created</th>
                <th>Anonymous</th>
              </tr>
            </thead>
            <tbody>
              {comments.map((comment) => (
                <tr key={comment.id}>
                  <td>{comment.id}</td>
                  <td className="content-cell">{comment.content}</td>
                  <td>{comment.entity_type}</td>
                  <td className="uuid-cell">{comment.entity_uuid.substring(0, 8)}...</td>
                  <td>{new Date(comment.created_at).toLocaleDateString()}</td>
                  <td>{comment.is_anonymous ? 'Yes' : 'No'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        <h4>Ratings ({ratings.length})</h4>
        {ratings.length === 0 ? (
          <p className="empty-message">No ratings</p>
        ) : (
          <table className="data-table compact">
            <thead>
              <tr>
                <th>ID</th>
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
                  <td>{rating.id}</td>
                  <td>{rating.entity_type}</td>
                  <td className="uuid-cell">{rating.entity_uuid.substring(0, 8)}...</td>
                  <td>{rating.dimension}</td>
                  <td>{rating.score}</td>
                  <td>{new Date(rating.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
