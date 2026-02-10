/**
 * Authors array editor for source metadata
 *
 * Structure: [{name: string, role: "author", affiliation?: string}]
 * Role is always "author" (hardcoded internally)
 *
 * @param {Object} props
 * @param {Array} props.authors - Array of author objects
 * @param {Function} props.onChange - (authors: Array) => void
 */
export function AuthorsInput({ authors = [], onChange }) {
  const addAuthor = () => {
    onChange([...authors, { name: '', role: 'author', affiliation: '' }]);
  };

  const removeAuthor = (index) => {
    const updated = authors.filter((_, i) => i !== index);
    onChange(updated);
  };

  const updateAuthor = (index, field, value) => {
    const updated = [...authors];
    updated[index] = { ...updated[index], [field]: value, role: 'author' };
    onChange(updated);
  };

  return (
    <div className="node-creation-field">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
        <label className="node-creation-label" style={{ margin: 0 }}>Authors</label>
        <button
          type="button"
          onClick={addAuthor}
          style={{
            padding: '4px 8px',
            fontSize: '0.75rem',
            backgroundColor: 'var(--accent-blue)',
            color: 'var(--bg-secondary)',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          + Add Author
        </button>
      </div>

      {authors.length === 0 ? (
        <div style={{
          padding: '12px',
          textAlign: 'center',
          color: 'var(--text-secondary)',
          fontSize: '0.85rem',
          fontStyle: 'italic',
          backgroundColor: 'var(--bg-primary)',
          borderRadius: '4px',
          border: '1px dashed var(--attr-border)'
        }}>
          No authors added yet
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {authors.map((author, index) => (
            <div
              key={index}
              style={{
                padding: '8px',
                backgroundColor: 'var(--bg-primary)',
                borderRadius: '4px',
                border: '1px solid var(--attr-border)'
              }}
            >
              <div style={{ display: 'flex', gap: '8px', alignItems: 'start' }}>
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <input
                    type="text"
                    className="node-creation-input"
                    placeholder="Author name"
                    value={author.name || ''}
                    onChange={(e) => updateAuthor(index, 'name', e.target.value)}
                    style={{ fontSize: '0.85rem' }}
                  />
                  <input
                    type="text"
                    className="node-creation-input"
                    placeholder="Affiliation (optional)"
                    value={author.affiliation || ''}
                    onChange={(e) => updateAuthor(index, 'affiliation', e.target.value)}
                    style={{ fontSize: '0.85rem' }}
                  />
                </div>
                <button
                  type="button"
                  onClick={() => removeAuthor(index)}
                  style={{
                    padding: '4px 8px',
                    fontSize: '0.75rem',
                    backgroundColor: 'transparent',
                    color: '#ff4444',
                    border: '1px solid #ff4444',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    whiteSpace: 'nowrap'
                  }}
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
