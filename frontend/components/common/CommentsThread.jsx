import { useState, useEffect } from 'react';
import { createComment, rateEntity, fetchEntityRatings, updateComment, deleteComment } from '../../APInterface/api.js';
import { useAuth } from '../../utilities/AuthContext.jsx';

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
 * Build nested tree structure from flat comment array
 * @param {Array} comments - Flat array of comments with parent_comment field
 * @returns {Array} - Nested array with replies property on each comment
 */
function buildCommentTree(comments) {
  const commentMap = new Map();
  const roots = [];

  // First pass: create map and initialize replies array
  comments.forEach(comment => {
    commentMap.set(comment.id, { ...comment, replies: [] });
  });

  // Second pass: build tree structure
  comments.forEach(comment => {
    const node = commentMap.get(comment.id);
    if (comment.parent_comment) {
      const parent = commentMap.get(comment.parent_comment);
      if (parent) {
        parent.replies.push(node);
      } else {
        // Parent not in list (maybe filtered), treat as root
        roots.push(node);
      }
    } else {
      roots.push(node);
    }
  });

  return roots;
}

/**
 * Single comment item with voting and reply
 */
function CommentItem({ comment, token, user, entityUuid, entityType, onCommentAdded, depth = 0 }) {
  const [showReplyInput, setShowReplyInput] = useState(false);
  const [replyContent, setReplyContent] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [userVote, setUserVote] = useState(null);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(comment.content || '');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // Backend now provides is_own field based on request user
  const isOwnComment = comment.is_own;

  // Fetch user's existing vote on mount
  useEffect(() => {
    const loadUserVote = async () => {
      if (!token) return;

      const response = await fetchEntityRatings(String(comment.id), null, token);
      if (!response.error && response.data?.user_score != null) {
        setUserVote(response.data.user_score);
      }
    };

    loadUserVote();
  }, [comment.id, token]);

  const hasReplies = comment.replies && comment.replies.length > 0;
  const totalReplies = hasReplies ? countAllReplies(comment) : 0;

  function countAllReplies(c) {
    if (!c.replies) return 0;
    return c.replies.reduce((sum, r) => sum + 1 + countAllReplies(r), 0);
  }

  const handleReplySubmit = async () => {
    if (!replyContent.trim() || !token) return;

    setSubmitting(true);
    const response = await createComment(token, {
      entity_uuid: entityUuid,
      entity_type: entityType,
      content: replyContent.trim(),
      parent_comment: comment.id
    });

    if (!response.error) {
      setReplyContent('');
      setShowReplyInput(false);
      if (onCommentAdded) onCommentAdded();
    }
    setSubmitting(false);
  };

  const handleVote = async (score) => {
    if (!token) return;

    // Rate the comment (entity_type='comment', entity_uuid=comment.id as string)
    await rateEntity(token, {
      entity_uuid: String(comment.id),
      entity_type: 'comment',
      score: score
    });
    setUserVote(score);
  };

  const handleEdit = async () => {
    if (!editContent.trim() || !token) return;

    setSubmitting(true);
    const response = await updateComment(token, comment.id, { content: editContent.trim() });

    if (!response.error) {
      setIsEditing(false);
      if (onCommentAdded) onCommentAdded();
    }
    setSubmitting(false);
  };

  const handleDelete = async () => {
    if (!token) return;

    setSubmitting(true);
    const response = await deleteComment(token, comment.id);

    if (!response.error) {
      setShowDeleteConfirm(false);
      if (onCommentAdded) onCommentAdded();
    }
    setSubmitting(false);
  };

  return (
    <div className="comment-thread-item">
      <div className={`comment-item ${depth > 0 ? 'comment-reply' : ''} ${isCollapsed ? 'collapsed' : ''}`}>
        {/* Collapse toggle */}
        <button
          className="collapse-toggle"
          onClick={() => setIsCollapsed(!isCollapsed)}
          title={isCollapsed ? 'Expand' : 'Collapse'}
        >
          {isCollapsed ? '[+]' : '[-]'}
        </button>

        {isCollapsed ? (
          /* Collapsed view - single line summary */
          <div className="comment-collapsed">
            <span className="comment-author">
              {isOwnComment ? 'you' : comment.username}
            </span>
            <span className="comment-dot">·</span>
            <span className="collapsed-info">
              {totalReplies > 0
                ? `${totalReplies + 1} comments collapsed`
                : 'comment collapsed'
              }
            </span>
          </div>
        ) : (
          /* Expanded view - full comment */
          <>
            <div className="comment-vote">
              <button
                className={`vote-btn upvote ${userVote === 100 ? 'active' : ''}`}
                onClick={() => handleVote(100)}
                disabled={!user}
                title={user ? 'Upvote' : 'Log in to vote'}
              >
                ▲
              </button>
              <button
                className={`vote-btn downvote ${userVote === 0 ? 'active' : ''}`}
                onClick={() => handleVote(0)}
                disabled={!user}
                title={user ? 'Downvote' : 'Log in to vote'}
              >
                ▼
              </button>
            </div>

            <div className="comment-body">
              <div className="comment-header">
                <span className="comment-author">
                  {isOwnComment ? 'you' : comment.username}
                </span>
                <span className="comment-dot">·</span>
                <span className="comment-timestamp">{formatRelativeTime(comment.timestamp)}</span>
              </div>

              {isEditing ? (
                /* Edit mode */
                <div className="edit-input-container">
                  <textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    rows={3}
                    disabled={submitting}
                  />
                  <div className="edit-input-actions">
                    <button
                      className="cancel-btn"
                      onClick={() => {
                        setIsEditing(false);
                        setEditContent(comment.content || '');
                      }}
                    >
                      Cancel
                    </button>
                    <button
                      className="submit-btn"
                      onClick={handleEdit}
                      disabled={submitting || !editContent.trim()}
                    >
                      {submitting ? 'Saving...' : 'Save'}
                    </button>
                  </div>
                </div>
              ) : (
                <div className="comment-content">
                  {comment.display_content}
                </div>
              )}

              <div className="comment-actions">
                {user && !isEditing && (
                  <button
                    className="action-btn"
                    onClick={() => setShowReplyInput(!showReplyInput)}
                  >
                    Reply
                  </button>
                )}
                {isOwnComment && !isEditing && !comment.is_deleted && (
                  <>
                    <button
                      className="action-btn"
                      onClick={() => setIsEditing(true)}
                    >
                      Edit
                    </button>
                    {showDeleteConfirm ? (
                      <>
                        <button
                          className="action-btn delete-confirm"
                          onClick={handleDelete}
                          disabled={submitting}
                        >
                          {submitting ? '...' : 'Confirm'}
                        </button>
                        <button
                          className="action-btn"
                          onClick={() => setShowDeleteConfirm(false)}
                        >
                          Cancel
                        </button>
                      </>
                    ) : (
                      <button
                        className="action-btn"
                        onClick={() => setShowDeleteConfirm(true)}
                      >
                        Delete
                      </button>
                    )}
                  </>
                )}
              </div>

              {showReplyInput && (
                <div className="reply-input-container">
                  <textarea
                    value={replyContent}
                    onChange={(e) => setReplyContent(e.target.value)}
                    placeholder="Write a reply..."
                    rows={3}
                    disabled={submitting}
                  />
                  <div className="reply-input-actions">
                    <button
                      className="cancel-btn"
                      onClick={() => {
                        setShowReplyInput(false);
                        setReplyContent('');
                      }}
                    >
                      Cancel
                    </button>
                    <button
                      className="submit-btn"
                      onClick={handleReplySubmit}
                      disabled={submitting || !replyContent.trim()}
                    >
                      {submitting ? 'Posting...' : 'Reply'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Render nested replies - hidden when collapsed */}
      {!isCollapsed && hasReplies && (
        <div className="comment-replies-container">
          {comment.replies.map(reply => (
            <CommentItem
              key={reply.id}
              comment={reply}
              token={token}
              user={user}
              entityUuid={entityUuid}
              entityType={entityType}
              onCommentAdded={onCommentAdded}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * CommentsThread component
 * Displays a list of comments with sort controls and new comment input
 *
 * @param {Object} props
 * @param {Array} props.comments - Array of comment objects
 * @param {string} props.sortBy - Current sort: 'timestamp' | 'score'
 * @param {Function} props.onSortChange - Callback when sort changes
 * @param {string} props.entityUuid - UUID of the entity being commented on
 * @param {string} props.entityType - Type of entity: 'claim' | 'source' | 'connection'
 * @param {Function} props.onCommentAdded - Callback to refresh comments after adding
 */
export function CommentsThread({ comments, sortBy, onSortChange, entityUuid, entityType, onCommentAdded }) {
  const { user, token } = useAuth();
  const [newComment, setNewComment] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmitComment = async () => {
    if (!newComment.trim() || !token) return;

    setSubmitting(true);
    const response = await createComment(token, {
      entity_uuid: entityUuid,
      entity_type: entityType,
      content: newComment.trim()
    });

    if (!response.error) {
      setNewComment('');
      if (onCommentAdded) onCommentAdded();
    }
    setSubmitting(false);
  };

  // Build nested tree structure from flat comments
  const commentTree = buildCommentTree(comments);

  return (
    <div className="comments-section">
      {/* New comment input */}
      {user ? (
        <div className="new-comment-container">
          <textarea
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="Add a comment..."
            rows={3}
            disabled={submitting}
          />
          <div className="new-comment-actions">
            <button
              className="submit-btn"
              onClick={handleSubmitComment}
              disabled={submitting || !newComment.trim()}
            >
              {submitting ? 'Posting...' : 'Comment'}
            </button>
          </div>
        </div>
      ) : (
        <div className="login-prompt">Log in to comment</div>
      )}

      {/* Sort controls */}
      <div className="comments-sort">
        <span className="sort-label">Sort by:</span>
        <button
          className={sortBy === 'timestamp' ? 'active' : ''}
          onClick={() => onSortChange('timestamp')}
        >
          Newest
        </button>
        <button
          className={sortBy === 'score' ? 'active' : ''}
          onClick={() => onSortChange('score')}
        >
          Top
        </button>
      </div>

      {/* Comments list */}
      <div className="comments-list">
        {commentTree.length === 0 ? (
          <div className="no-comments">No comments yet. Be the first!</div>
        ) : (
          commentTree.map(comment => (
            <CommentItem
              key={comment.id}
              comment={comment}
              token={token}
              user={user}
              entityUuid={entityUuid}
              entityType={entityType}
              onCommentAdded={onCommentAdded}
            />
          ))
        )}
      </div>
    </div>
  );
}
