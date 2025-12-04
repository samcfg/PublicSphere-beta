import { useNavigate } from 'react-router-dom';
import '../../styles/components/IncomingConnectionsSidebar.css';

/**
 * IncomingConnectionsSidebar - Compact list of connections pointing to current node
 *
 * @param {Object} props
 * @param {Array<Object>} props.connections - Array of connection objects
 *   Each: {connectionId, fromNodes: [{id, content, type}], logicType, compositeId}
 */
export function IncomingConnectionsSidebar({ connections }) {
  const navigate = useNavigate();

  if (!connections || connections.length === 0) {
    return (
      <div className="incoming-sidebar">
        <div className="sidebar-header">Incoming Connections</div>
        <div className="sidebar-empty">No incoming connections</div>
      </div>
    );
  }

  const handleConnectionClick = (connectionId) => {
    navigate(`/connectionview?id=${connectionId}`);
  };

  return (
    <div className="incoming-sidebar">
      <div className="sidebar-header">
        Incoming Connections ({connections.length})
      </div>

      <div className="sidebar-connections-list">
        {connections.map((conn) => {
          const isNegative = conn.logicType === 'NOT' || conn.logicType === 'NAND';
          const isCompound = conn.fromNodes.length > 1;

          return (
            <div
              key={conn.connectionId}
              className="sidebar-connection-item"
              onClick={() => handleConnectionClick(conn.connectionId)}
            >
              {/* Logic type badge */}
              <div
                className={`sidebar-logic-badge ${isNegative ? 'negative' : 'positive'}`}
              >
                {conn.logicType || 'AND'}
              </div>

              {/* Source nodes preview */}
              <div className="sidebar-sources">
                {isCompound && (
                  <div className="sidebar-compound-indicator">
                    {conn.fromNodes.length} sources
                  </div>
                )}
                {conn.fromNodes.slice(0, 4).map((node, idx) => (
                  <div key={node.id} className="sidebar-source-preview">
                    <span className={`node-type-indicator ${node.type}`}>
                      {node.type === 'source' ? 'S' : 'C'}
                    </span>
                    <span className="source-content-preview">
                      {node.content.length > 128
                        ? node.content.substring(0, 125) + '...'
                        : node.content}
                    </span>
                  </div>
                ))}
                {conn.fromNodes.length > 4 && (
                  <div className="sidebar-more-sources">
                    +{conn.fromNodes.length - 4} more
                  </div>
                )}
              </div>

              {/* Arrow indicator */}
              <div className="sidebar-arrow">→</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
