import { UserAttribution } from './UserAttribution.jsx';
import { CommentsRating } from './CommentsRating.jsx';

/**
 * NodeDisplay - Displays node content in centered, poem-like format
 * Shows attribution, optional URL, content, and comments/ratings
 * Designed for standalone node views and connection view pages
 *
 * @param {Object} props
 * @param {string} props.nodeId - Node UUID
 * @param {string} props.nodeType - 'claim' | 'source'
 * @param {string} props.content - Node content text
 * @param {string} props.url - Optional URL (for source nodes)
 * @param {Object} props.containerStyle - Optional style overrides for outer container
 * @param {Object} props.contentStyle - Optional style overrides for inner content container
 */
export function NodeDisplay({ nodeId, nodeType, content, url, containerStyle = {}, contentStyle = {} }) {
  const borderColor = nodeType === 'source' ? 'var(--accent-blue-dark)' : 'var(--accent-blue)';

  return (
    <div style={{
      position: 'relative',
      border: `0.5px solid ${borderColor}`,
      padding: '60px 60px',
      ...containerStyle
    }}>
      <div style={{
        position: 'relative',
        textAlign: 'center',
        maxWidth: '800px',
        whiteSpace: 'pre-wrap',
        ...contentStyle
      }}>
        <div style={{
          position: 'absolute',
          top: '-50px',
          left: '0',
          fontSize: '14px'
        }}>
          <UserAttribution
            entityUuid={nodeId}
            entityType={nodeType}
            showTimestamp={true}
          />
        </div>
        {url && (
          <div style={{
            position: 'absolute',
            top: '-50px',
            right: '-50px',
            fontSize: '12px',
            maxWidth: '300px',
            wordWrap: 'break-word',
            textAlign: 'right'
          }}>
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: 'var(--accent-blue)', textDecoration: 'none' }}
            >
              {url}
            </a>
          </div>
        )}
        {content}
      </div>
      <div style={{
        position: 'absolute',
        bottom: '0',
        right: '0',
        maxWidth: '280px'
      }}>
        <CommentsRating
          entityUuid={nodeId}
          entityType={nodeType}
          tabsOnly={false}
          standalone={true}
          entityColor={borderColor}
        />
      </div>
    </div>
  );
}
