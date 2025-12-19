import '../../styles/components/node-creation-panel.css';

/**
 * Connection creation box - positioned to the right of clicked node
 * Shows relationship selector and connection notes
 * Highlight color reflects relationship type (support=green, contradict=red)
 *
 * @param {Object} props
 * @param {boolean} props.isCompound - Whether in compound mode
 * @param {Function} props.onCompoundToggle - Toggle compound mode
 * @param {string} props.relationship - Selected relationship ('supports' or 'contradicts')
 * @param {Function} props.onRelationshipChange - Callback when relationship changes
 * @param {string} props.logicType - Logic type for compound ('AND' or 'NAND')
 * @param {Function} props.onLogicTypeChange - Callback when logic type changes
 * @param {string} props.connectionNotes - Connection notes text
 * @param {Function} props.onConnectionNotesChange - Callback when notes change
 * @param {number} props.nodeCount - Number of nodes in compound connection
 * @param {Function} props.onNodeCountChange - Callback to change node count
 */
export function ConnectionBox({
  isCompound,
  onCompoundToggle,
  relationship,
  onRelationshipChange,
  logicType,
  onLogicTypeChange,
  connectionNotes,
  onConnectionNotesChange,
  nodeCount,
  onNodeCountChange
}) {
  // Simple binary choice for simple mode
  const relationshipOptions = [
    { value: 'supports', label: 'supports' },
    { value: 'contradicts', label: 'contradicts' }
  ];

  // Logic types for compound mode (AND=supports, NAND=contradicts)
  const logicTypeOptions = [
    { value: 'AND', label: 'AND', color: 'var(--accent-green)' },
    { value: 'NAND', label: 'NAND', color: 'var(--accent-red)' }
  ];

  // Determine highlight color based on mode
  const getHighlightColor = () => {
    if (isCompound) {
      if (!logicType) return 'var(--accent-blue)'; // Default neutral
      if (logicType === 'NAND') return 'var(--accent-red)';
      return 'var(--accent-green)'; // AND
    } else {
      if (!relationship) return 'var(--accent-blue)'; // Default neutral
      if (relationship === 'contradicts') return 'var(--accent-red)';
      return 'var(--accent-green)'; // supports
    }
  };

  return (
    <div className="node-creation-panel" onClick={(e) => e.stopPropagation()}>
      <div className="node-creation-highlight" style={{ backgroundColor: getHighlightColor() }}>
        <div className="node-creation-inner" style={{ width: '220px' }}>
          <div className="node-creation-header">
            <h2 className="node-creation-title" style={{ color: getHighlightColor() }}>Connection</h2>
          </div>

          <div className="node-creation-content">
            {/* Compound mode toggle */}
            <div className="node-creation-field">
              <label className="node-creation-option" style={{ cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={isCompound}
                  onChange={onCompoundToggle}
                />
                <span style={{ fontSize: '11px' }}>Compound Connection</span>
              </label>
            </div>

            {/* Simple mode: Relationship selection */}
            {!isCompound && (
              <div className="node-creation-field">
                <label className="node-creation-label">Relationship</label>
                <div className="node-creation-options">
                  {relationshipOptions.map(opt => (
                    <label key={opt.value} className="node-creation-option">
                      <input
                        type="radio"
                        name="relationship"
                        value={opt.value}
                        checked={relationship === opt.value}
                        onChange={() => onRelationshipChange(opt.value)}
                      />
                      <span>This <em>{opt.label}</em></span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* Compound mode: Logic type + node count */}
            {isCompound && (
              <>
                <div className="node-creation-field">
                  <label className="node-creation-label">Logic Type</label>
                  <div className="node-creation-options">
                    {logicTypeOptions.map(opt => (
                      <label key={opt.value} className="node-creation-option">
                        <input
                          type="radio"
                          name="logicType"
                          value={opt.value}
                          checked={logicType === opt.value}
                          onChange={() => onLogicTypeChange(opt.value)}
                        />
                        <span style={{ color: opt.color, fontWeight: 'bold' }}>{opt.label}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div className="node-creation-field">
                  <label className="node-creation-label">Node Count</label>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <button
                      className="node-creation-btn"
                      onClick={() => onNodeCountChange(Math.max(2, nodeCount - 1))}
                      disabled={nodeCount <= 2}
                      style={{ padding: '4px 8px', fontSize: '14px' }}
                    >
                      −
                    </button>
                    <span style={{ fontWeight: 'bold', minWidth: '20px', textAlign: 'center' }}>
                      {nodeCount}
                    </span>
                    <button
                      className="node-creation-btn"
                      onClick={() => onNodeCountChange(nodeCount + 1)}
                      style={{ padding: '4px 8px', fontSize: '14px' }}
                    >
                      +
                    </button>
                  </div>
                </div>
              </>
            )}

            {/* Connection notes - always visible, more compact */}
            <div className="node-creation-field">
              <label className="node-creation-label">
                Notes
                <span style={{ fontSize: '11px', opacity: 0.6, marginLeft: '6px' }}>
                  ({connectionNotes.length}/500)
                </span>
              </label>
              <textarea
                className="node-creation-textarea node-creation-notes"
                placeholder="Why this connection holds..."
                value={connectionNotes}
                onChange={(e) => {
                  if (e.target.value.length <= 500) {
                    onConnectionNotesChange(e.target.value);
                  }
                }}
                maxLength={500}
                style={{ minHeight: '60px' }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
