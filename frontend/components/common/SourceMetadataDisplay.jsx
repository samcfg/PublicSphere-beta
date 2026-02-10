import { getSourceMetadataFields } from '../../utilities/formatters.js';

/**
 * SourceMetadataDisplay - Displays structured metadata for source nodes
 * Used by both NodeDisplay (full view) and OnClickNode (compact tooltip)
 *
 * @param {Object} props
 * @param {Object} props.sourceData - Full source object with all metadata fields
 * @param {boolean} props.loading - Whether metadata is still loading
 * @param {boolean} props.compact - Use compact styling for tooltips (smaller fonts, tighter spacing)
 * @param {React.ReactNode} props.fallback - Optional fallback content when no metadata available
 */
export function SourceMetadataDisplay({ sourceData, loading = false, compact = false, fallback = null }) {
  const fields = getSourceMetadataFields(sourceData);

  // Styling based on compact mode
  const styles = compact ? {
    container: { display: 'flex', flexDirection: 'column', gap: '6px' },
    labelFont: '9px',
    valueFont: '11px',
    labelMinWidth: '80px',
    rowGap: '6px',
    textGap: '2px',
    textPaddingLeft: '8px',
    lineHeight: '1.3'
  } : {
    container: { textAlign: 'left', display: 'flex', flexDirection: 'column', gap: '12px' },
    labelFont: 'inherit',
    valueFont: 'inherit',
    labelMinWidth: '140px',
    rowGap: '8px',
    textGap: '4px',
    textPaddingLeft: '20px',
    lineHeight: '1.4'
  };

  if (loading) {
    return (
      <div style={{
        fontSize: compact ? '11px' : 'inherit',
        color: 'var(--text-secondary)',
        fontStyle: 'italic'
      }}>
        Loading metadata...
      </div>
    );
  }

  if (!fields || fields.length === 0) {
    return fallback || null;
  }

  return (
    <div style={styles.container}>
      {fields.map((field, index) => {
        // URL field - clickable link
        if (field.label === 'URL') {
          return (
            <div key={index} style={{
              display: 'flex',
              gap: styles.rowGap,
              alignItems: 'flex-start'
            }}>
              <span style={{
                fontSize: styles.labelFont,
                color: 'var(--text-muted)',
                minWidth: styles.labelMinWidth,
                fontWeight: '600'
              }}>
                {field.label}:
              </span>
              <a
                href={field.value}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  fontSize: styles.valueFont,
                  color: 'var(--accent-blue)',
                  textDecoration: 'none',
                  wordBreak: 'break-all',
                  lineHeight: styles.lineHeight
                }}
              >
                {field.value}
              </a>
            </div>
          );
        }

        // Long text fields (Excerpt, Content) - vertical layout with indentation
        if (field.label === 'Excerpt' || field.label === 'Content') {
          return (
            <div key={index} style={{
              display: 'flex',
              flexDirection: 'column',
              gap: styles.textGap
            }}>
              <span style={{
                fontSize: styles.labelFont,
                color: 'var(--text-muted)',
                fontWeight: '600'
              }}>
                {field.label}:
              </span>
              <div style={{
                fontSize: styles.valueFont,
                color: compact ? 'var(--text-secondary)' : 'var(--text-primary)',
                lineHeight: styles.lineHeight,
                paddingLeft: styles.textPaddingLeft,
                whiteSpace: 'pre-wrap'
              }}>
                {field.value}
              </div>
            </div>
          );
        }

        // Default field - horizontal label:value
        return (
          <div key={index} style={{
            display: 'flex',
            gap: styles.rowGap,
            alignItems: 'flex-start'
          }}>
            <span style={{
              fontSize: styles.labelFont,
              color: compact ? 'var(--text-muted)' : 'var(--text-secondary)',
              minWidth: styles.labelMinWidth,
              fontWeight: '600'
            }}>
              {field.label}:
            </span>
            <span style={{
              fontSize: styles.valueFont,
              color: 'var(--text-primary)',
              lineHeight: styles.lineHeight,
              flex: 1
            }}>
              {field.value}
            </span>
          </div>
        );
      })}
    </div>
  );
}
