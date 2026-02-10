/**
 * Simple form for creating/editing claims
 *
 * @param {Object} props
 * @param {string} props.content - Claim text
 * @param {Function} props.onContentChange - (value: string) => void
 * @param {React.ReactNode} props.error - Error message or JSX
 */
export function ClaimForm({ content, onContentChange, error }) {
  return (
    <>
      <div className="node-creation-field">
        <label className="node-creation-label">Claim</label>
        <textarea
          className="node-creation-textarea"
          placeholder="State the claim..."
          value={content}
          onChange={(e) => onContentChange(e.target.value)}
        />
      </div>

      {error && (
        <div className="node-creation-error">
          {error}
        </div>
      )}
    </>
  );
}
