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
 * @param {string} props.entityColor - Highlight color for tabs and accents (from entity type)
 * @param {boolean} props.standalone - If true, renders in standalone page mode (content expands downward)
 */
export function CommentsRating({ entityUuid, entityType, onTabChange, tabsOnly = false, entityColor, standalone = false }) {
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
    const response = await fetchEntityComments(entityUuid, commentSort, token);

    if (!response.error && response.data) {
      setComments(response.data);
    }
    setLoadingComments(false);
  };

  useEffect(() => {
    loadComments();
  }, [entityUuid, commentSort, token]);

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
    // Toggle: clicking active tab closes it
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

  // Default to green if no color provided (backwards compatibility)
  const tabBarColor = entityColor || 'var(--accent-green)';

  return (
    <div className={`comments-rating-container ${standalone ? 'cr-standalone' : ''}`} style={{ '--entity-color': tabBarColor }}>
      {/* Tab bar */}
      <div className="cr-tabs" style={{ backgroundColor: tabBarColor }}>
        <label className="cr-tab">
          <input
            type="radio"
            name="cr-tab"
            checked={activeTab === 'ratings'}
            onChange={() => handleTabClick('ratings')}
            onClick={(e) => {
              if (activeTab === 'ratings') {
                e.preventDefault();
                handleTabClick('ratings');
              }
            }}
          />
          <span className="tab-label">
            <div className="rating-summary">
              <span className="rating-text">{loadingRatings ? '...' : `${avgRating} (${ratingCount})`}</span>
              <div className="rating-bar-mini">
                <div className="bar-fill" style={{ width: `${avgRating}%` }} />
                {ratings?.user_score != null && (
                  <div className="user-mark" style={{ left: `${ratings.user_score}%` }} />
                )}
              </div>
            </div>
          </span>
        </label>

        <label className="cr-tab">
          <input
            type="radio"
            name="cr-tab"
            checked={activeTab === 'comments'}
            onChange={() => handleTabClick('comments')}
            onClick={(e) => {
              if (activeTab === 'comments') {
                e.preventDefault();
                handleTabClick('comments');
              }
            }}
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
                <div className="user-rating">
                  {user ? (
                    <div className="rating-input-slider">
                      <label>Your rating: {ratingInput || '0'}</label>
                      <div className="rating-bar-input">
                        <input
                          type="range"
                          min="0"
                          max="100"
                          value={ratingInput || 0}
                          onChange={(e) => setRatingInput(e.target.value)}
                          onMouseUp={handleRatingSubmit}
                          onTouchEnd={handleRatingSubmit}
                          disabled={submittingRating}
                        />
                        <div className="bar-track">
                          <div className="bar-fill-input" style={{ width: `${ratingInput || 0}%` }} />
                        </div>
                      </div>
                    </div>
                  ) : (
                    <span>Log in to rate</span>
                  )}
                </div>
                <div className="rating-stats">
                  {ratings?.distribution && (() => {
                    const maxCount = Math.max(...Object.values(ratings.distribution));
                    return (
                      <div className="rating-distribution">
                        <div className="distribution-label">Distribution:</div>
                        <div className="distribution-bars-vertical">
                          {[
                            { key: '0-20' },
                            { key: '20-40' },
                            { key: '40-60' },
                            { key: '60-80' },
                            { key: '80-100' }
                          ].map(({ key }) => {
                            const count = ratings.distribution[key] || 0;
                            const heightPercent = maxCount > 0 ? (count / maxCount) * 100 : 0;
                            return (
                              <div key={key} className="distribution-bar-column">
                                <div className="bar-vertical-container">
                                  <div
                                    className="bar-vertical"
                                    style={{ height: `${heightPercent}%` }}
                                    title={`${count} rating${count !== 1 ? 's' : ''} (${key})`}
                                  />
                                </div>
                              </div>
                            );
                          })}
                        </div>
                        <div className="distribution-axis">
                          <span>0</span>
                          <span>100</span>
                        </div>
                      </div>
                    );
                  })()}
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
