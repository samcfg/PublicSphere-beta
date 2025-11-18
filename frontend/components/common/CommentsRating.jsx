import { useState, useEffect } from 'react';
import { fetchEntityRatings, fetchEntityComments } from '../../APInterface/api.js';
import { useAuth } from '../../utilities/AuthContext.jsx';

/**
 * CommentsRating component
 * Self-contained ratings and comments display with expandable dropdowns
 * Fetches data internally for reusability across node/edge tooltips
 *
 * @param {Object} props
 * @param {string} props.entityUuid - UUID of the entity
 * @param {string} props.entityType - 'claim' | 'source' | 'connection'
 */
export function CommentsRating({ entityUuid, entityType }) {
  const { user } = useAuth();
  const [ratings, setRatings] = useState(null);
  const [comments, setComments] = useState([]);
  const [loadingRatings, setLoadingRatings] = useState(true);
  const [loadingComments, setLoadingComments] = useState(true);
  const [ratingsExpanded, setRatingsExpanded] = useState(false);
  const [commentsExpanded, setCommentsExpanded] = useState(false);

  // Fetch ratings
  useEffect(() => {
    const loadRatings = async () => {
      setLoadingRatings(true);
      const response = await fetchEntityRatings(entityUuid);

      if (!response.error && response.data) {
        setRatings(response.data);
      }
      setLoadingRatings(false);
    };

    loadRatings();
  }, [entityUuid]);

  // Fetch comments
  useEffect(() => {
    const loadComments = async () => {
      setLoadingComments(true);
      const response = await fetchEntityComments(entityUuid);

      if (!response.error && response.data) {
        setComments(response.data);
      }
      setLoadingComments(false);
    };

    loadComments();
  }, [entityUuid]);

  const avgRating = ratings?.avg_score?.toFixed(1) || 'N/A';
  const ratingCount = ratings?.count || 0;
  const commentCount = comments.length;

  return (
    <div className="comments-rating-container">
      {/* Ratings Section */}
      <div className="rating-section">
        <button
          className="rating-toggle"
          onClick={() => setRatingsExpanded(!ratingsExpanded)}
          disabled={loadingRatings}
        >
          <span className="rating-icon">⭐</span>
          <span className="rating-summary">
            {loadingRatings ? '...' : `${avgRating} (${ratingCount})`}
          </span>
        </button>

        {ratingsExpanded && !loadingRatings && (
          <div className="rating-dropdown">
            <div className="rating-stats">
              <div className="stat-row">
                <span>Average:</span>
                <span>{avgRating}</span>
              </div>
              <div className="stat-row">
                <span>Ratings:</span>
                <span>{ratingCount}</span>
              </div>
              {ratings?.stddev && (
                <div className="stat-row">
                  <span>Std Dev:</span>
                  <span>{ratings.stddev.toFixed(1)}</span>
                </div>
              )}
            </div>
            {user && (
              <div className="user-rating">
                <span>Your rating: [TODO]</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Comments Section */}
      <div className="comments-section">
        <button
          className="comments-toggle"
          onClick={() => setCommentsExpanded(!commentsExpanded)}
          disabled={loadingComments}
        >
          <span className="comments-icon">💬</span>
          <span className="comments-summary">
            {loadingComments ? '...' : `${commentCount}`}
          </span>
        </button>

        {commentsExpanded && !loadingComments && (
          <div className="comments-dropdown">
            {commentCount === 0 ? (
              <div className="no-comments">No comments yet</div>
            ) : (
              <div className="comments-list">
                {comments.map(comment => (
                  <div key={comment.id} className="comment-item">
                    <div className="comment-header">
                      <span className="comment-author">{comment.username}</span>
                      <span className="comment-timestamp">
                        {new Date(comment.timestamp).toLocaleDateString()}
                      </span>
                    </div>
                    <div className="comment-content">
                      {comment.display_content}
                    </div>
                    {comment.reply_count > 0 && (
                      <div className="comment-replies">
                        {comment.reply_count} {comment.reply_count === 1 ? 'reply' : 'replies'}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
