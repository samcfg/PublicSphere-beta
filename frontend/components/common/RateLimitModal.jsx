/**
 * RateLimitModal component
 * Displays when user hits API rate limit (429 status)
 * Uses modal1.css aesthetic for consistency
 */
export function RateLimitModal({ onClose }) {
  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="modal-backdrop" onClick={handleBackdropClick}>
      <div className="modal-card">
        <h2 className="modal-title">Rate Limit Exceeded</h2>

        <div className="modal-content">
          <p>You've made too many requests in a short time.</p>
          <p>Please wait a moment before trying again.</p>
        </div>

        <button className="modal-button" onClick={onClose}>
          OK
        </button>
      </div>
    </div>
  );
}
