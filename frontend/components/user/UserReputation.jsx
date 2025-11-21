import { useState, useEffect } from 'react';
import { useAuth } from '../../utilities/AuthContext.jsx';
import { fetchUserProfile } from '../../APInterface/api.js';

/**
 * UserReputation component
 * Shows reputation score, contribution counts, and formula explanation
 * Design spec: "Reputation is two words 'value' 'type'"
 * - value = upvotes/downvotes + admin incidents (Phase 2 - ratings not yet implemented)
 * - type = sum(contribution type * number) e.g., "prolific reader" or "effective contributor"
 * 
 * USE THIS FOR CALCULATION: get_user_contributions()
 */
export function UserReputation() {
  const { token } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    setLoading(true);
    const response = await fetchUserProfile(token);

    if (response.error) {
      setError(response.error);
      setLoading(false);
      return;
    }

    setProfile(response.data);
    setLoading(false);
  };

  if (loading) return <div className="loading">Loading reputation data...</div>;
  if (error) return <div className="error">Error: {error}</div>;
  if (!profile) return null;

  const { total_claims, total_sources, total_connections, reputation_score } = profile;

  // Calculate contribution type descriptor
  const getContributionType = () => {
    const total = total_claims + total_sources + total_connections;
    if (total === 0) return 'new';

    // Analyze contribution distribution
    const claimRatio = total_claims / total;
    const sourceRatio = total_sources / total;
    const connectionRatio = total_connections / total;

    if (total < 5) return 'novice';
    if (total >= 100) return 'prolific';
    if (total >= 50) return 'active';

    // Type based on what they contribute most
    if (sourceRatio > 0.5) return 'evidence-focused';
    if (claimRatio > 0.5) return 'claim-focused';
    if (connectionRatio > 0.4) return 'connector';

    return 'contributor';
  };

  const reputationType = getContributionType();

  return (
    <div className="user-reputation">
      <section className="reputation-summary">
        <h2>Reputation</h2>
        <div className="reputation-display">
          <span className="reputation-type">{reputationType}</span>
          <span className="reputation-score">{reputation_score}</span>
        </div>
      </section>

      <section className="contribution-breakdown">
        <h3>Contributions</h3>
        <div className="contribution-stats">
          <div className="stat-item">
            <span className="stat-label">Claims</span>
            <span className="stat-value">{total_claims}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Sources</span>
            <span className="stat-value">{total_sources}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Connections</span>
            <span className="stat-value">{total_connections}</span>
          </div>
        </div>
      </section>

      <section className="reputation-formula">
        <h3>Formula</h3>
        <div className="formula-explanation">
          <p className="formula-text">
            Reputation Score = Claims + Sources + Connections
          </p>
          <p className="formula-calculation">
            {reputation_score} = {total_claims} + {total_sources} + {total_connections}
          </p>
          <p className="formula-note">
            Type descriptor: Based on contribution count and distribution
          </p>
        </div>
      </section>

      <section className="reputation-disclaimer">
        <p className="disclaimer-text">
          * This calculation is an approximation with a large margin of error, and should
          be considered as a factor among others when evaluating user contributions.
        </p>
        <p className="disclaimer-note">
          Note: Ratings integration (upvotes/downvotes) will be added in Phase 2
        </p>
      </section>
    </div>
  );
}
