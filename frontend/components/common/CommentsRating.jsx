import { useState, useEffect } from 'react';
import { fetchEntityRatings, fetchEntityComments, rateEntity } from '../../APInterface/api.js';
import { useAuth } from '../../utilities/AuthContext.jsx';
import { CommentsThread } from './CommentsThread.jsx';
import '../../styles/components/CommentsRating.css';

/**
 * CommentsRating component
 * Tab-based ratings and comments display
 * Fetches data internally for reusability across node/edge tooltips
 *
 * @param {Object} props
 * @param {string} props.entityUuid - UUID of the entity
 * @param {string} props.entityType - 'claim' | 'source' | 'connection'
 * @param {Function} props.onTabChange - Callback when tab selection changes (tab: string | null)
 * @param {boolean} props.tabsOnly - If true, only render tabs without content panel
 */
export function CommentsRating({ entityUuid, entityType, onTabChange, tabsOnly = false }) {
  const { user, token } = useAuth();
  const [ratings, setRatings] = useState(null);
  const [comments, setComments] = useState([]);
  const [loadingRatings, setLoadingRatings] = useState(true);
  const [loadingComments, setLoadingComments] = useState(true);
  const [activeTab, setActiveTab] = useState(null); // 'ratings' | 'comments' | null
  const [ratingInput, setRatingInput] = useState('');
  const [submittingRating, setSubmittingRating] = useState(false);
  const [commentSort, setCommentSort] = useState('timestamp'); // 'timestamp' | 'score'

  // Fetch ratings
  useEffect(() => {
    const loadRatings = async () => {
      setLoadingRatings(true);
      const response = await fetchEntityRatings(entityUuid, null, token);

      if (!response.error && response.data) {
        setRatings(response.data);
      }
      setLoadingRatings(false);
    };

    loadRatings();
  }, [entityUuid, token]);

  // Fetch comments
  const loadComments = async () => {
    setLoadingComments(true);
    const response = await fetchEntityComments(entityUuid, commentSort);

    if (!response.error && response.data) {
      setComments(response.data);
    }
    setLoadingComments(false);
  };

  useEffect(() => {
    loadComments();
  }, [entityUuid, commentSort]);

  const avgRating = ratings?.avg_score?.toFixed(1) || 'N/A';
  const ratingCount = ratings?.count || 0;
  const commentCount = comments.length;

  // Pre-fill rating input when user's score loads
  useEffect(() => {
    if (ratings?.user_score != null) {
      setRatingInput(ratings.user_score.toString());
    } else {
      setRatingInput('');
    }
  }, [ratings?.user_score]);

  const handleTabClick = (tab) => {
    const newTab = activeTab === tab ? null : tab;
    setActiveTab(newTab);
    if (onTabChange) {
      onTabChange(newTab);
    }
  };

  const handleRatingSubmit = async () => {
    const score = parseFloat(ratingInput);
    if (isNaN(score) || score < 0 || score > 100) {
      return; // Invalid input
    }

    setSubmittingRating(true);
    const response = await rateEntity(token, {
      entity_uuid: entityUuid,
      entity_type: entityType,
      score: score
    });

    if (!response.error) {
      // Refresh ratings to get updated aggregates
      const refreshed = await fetchEntityRatings(entityUuid, null, token);
      if (!refreshed.error && refreshed.data) {
        setRatings(refreshed.data);
      }
    }
    setSubmittingRating(false);
  };

  return (
    <div className="comments-rating-container">
      {/* Tab bar */}
      <div className="cr-tabs">
        <label className="cr-tab">
          <input
            type="radio"
            name="cr-tab"
            checked={activeTab === 'ratings'}
            onChange={() => handleTabClick('ratings')}
          />
          <span className="tab-label">
            <span className="tab-icon">⭐</span>
            <span className="tab-summary">
              {loadingRatings ? '...' : `${avgRating} (${ratingCount})`}
            </span>
          </span>
        </label>

        <label className="cr-tab">
          <input
            type="radio"
            name="cr-tab"
            checked={activeTab === 'comments'}
            onChange={() => handleTabClick('comments')}
          />
          <span className="tab-label">
            <span className="tab-icon">💬</span>
            <span className="tab-summary">
              {loadingComments ? '...' : `${commentCount}`}
            </span>
          </span>
        </label>
      </div>

      {/* Content panel - only render if not tabsOnly mode */}
      {!tabsOnly && activeTab && (
        <div className="cr-content">
          {/* Ratings content */}
          {activeTab === 'ratings' && (
            loadingRatings ? (
              <div className="cr-loading">Loading...</div>
            ) : (
              <>
                <div className="rating-stats">
                  <div className="stat-row">
                    <span>Average:</span>
                    <span>{avgRating}</span>
                  </div>
                  <div className="stat-row">
                    <span>Ratings:</span>
                    <span>{ratingCount}</span>
                  </div>
                  {ratings?.stddev != null && (
                    <div className="stat-row">
                      <span>Std Dev:</span>
                      <span>{ratings.stddev.toFixed(1)}</span>
                    </div>
                  )}
                  {ratings?.distribution && (
                    <div className="rating-distribution">
                      <div className="stat-row"><span>0-20:</span><span>{ratings.distribution['0-20']}</span></div>
                      <div className="stat-row"><span>20-40:</span><span>{ratings.distribution['20-40']}</span></div>
                      <div className="stat-row"><span>40-60:</span><span>{ratings.distribution['40-60']}</span></div>
                      <div className="stat-row"><span>60-80:</span><span>{ratings.distribution['60-80']}</span></div>
                      <div className="stat-row"><span>80-100:</span><span>{ratings.distribution['80-100']}</span></div>
                    </div>
                  )}
                </div>
                <div className="user-rating">
                  {user ? (
                    <div className="rating-input-row">
                      <span>Your rating:</span>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        value={ratingInput}
                        onChange={(e) => setRatingInput(e.target.value)}
                        placeholder="0-100"
                        disabled={submittingRating}
                      />
                      <button
                        onClick={handleRatingSubmit}
                        disabled={submittingRating || !ratingInput}
                      >
                        {submittingRating ? '...' : (ratings?.user_score != null ? 'Update' : 'Submit')}
                      </button>
                    </div>
                  ) : (
                    <span>Log in to rate</span>
                  )}
                </div>
              </>
            )
          )}

          {/* Comments content */}
          {activeTab === 'comments' && (
            loadingComments ? (
              <div className="cr-loading">Loading...</div>
            ) : (
              <CommentsThread
                comments={comments}
                sortBy={commentSort}
                onSortChange={setCommentSort}
                entityUuid={entityUuid}
                entityType={entityType}
                onCommentAdded={loadComments}
              />
            )
          )}
        </div>
      )}
    </div>
  );
}
