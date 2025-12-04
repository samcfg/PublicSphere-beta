import { NodeDisplay } from './NodeDisplay.jsx';
import { UserAttribution } from './UserAttribution.jsx';
import { CommentsRating } from './CommentsRating.jsx';
import '../../styles/components/ConnectionDisplay.css';

/**
 * ConnectionDisplay - Displays connection between nodes with organic SVG curve
 * Handles simple (1 source) and compound (N sources) connections
 *
 * @param {Object} props
 * @param {string} props.connectionId - Connection UUID
 * @param {Array<Object>} props.fromNodes - Source nodes [{id, content, type, url}, ...]
 * @param {Object} props.toNode - Target node {id, content, type, url}
 * @param {string} props.logicType - 'AND'|'OR'|'NOT'|'NAND'
 * @param {string} props.notes - Optional connection notes
 * @param {string} props.compositeId - UUID for compound connections
 * @param {Object} props.containerStyle - Optional style overrides
 */
export function ConnectionDisplay({
  connectionId,
  fromNodes,
  toNode,
  logicType,
  notes,
  compositeId,
  containerStyle = {}
}) {
  // Determine if connection is negative
  const isNegative = logicType === 'NOT' || logicType === 'NAND';
  const curveColor = isNegative
    ? getComputedStyle(document.documentElement).getPropertyValue('--accent-red').trim() || '#e74c3c'
    : getComputedStyle(document.documentElement).getPropertyValue('--accent-green').trim() || '#68d391';

  const isCompound = fromNodes.length > 1;

  // Layout constants
  const CONTAINER_WIDTH = 1200;
  const CONTAINER_HEIGHT = isCompound ? 600 + (fromNodes.length - 1) * 200 : 400;
  const NODE_DISPLAY_WIDTH = 400;
  const SOURCE_X = 50;
  const TARGET_X = CONTAINER_WIDTH - NODE_DISPLAY_WIDTH - 50;
  const CURVE_START_X = SOURCE_X + NODE_DISPLAY_WIDTH;
  const CURVE_END_X = TARGET_X;
  const HORIZONTAL_GAP = CURVE_END_X - CURVE_START_X;

  // Calculate source node positions
  const sourcePositions = [];
  if (isCompound) {
    const stackHeight = fromNodes.length * 200 + (fromNodes.length - 1) * 20;
    const startY = (CONTAINER_HEIGHT - stackHeight) / 2 + 100;
    fromNodes.forEach((node, idx) => {
      sourcePositions.push({
        node,
        x: SOURCE_X,
        y: startY + idx * 220,
        centerY: startY + idx * 220 + 100
      });
    });
  } else {
    sourcePositions.push({
      node: fromNodes[0],
      x: SOURCE_X,
      y: CONTAINER_HEIGHT / 2 - 100,
      centerY: CONTAINER_HEIGHT / 2
    });
  }

  // Target position
  const targetY = CONTAINER_HEIGHT / 2 - 100;
  const targetCenterY = CONTAINER_HEIGHT / 2;

  // Calculate source stack center (for curve convergence)
  const sourceStackCenterY = sourcePositions.reduce((sum, pos) => sum + pos.centerY, 0) / sourcePositions.length;

  // Bezier curve calculation
  const generateCurvePath = (startX, startY, endX, endY, offset = 0) => {
    const verticalDiff = Math.abs(endY - startY);
    const verticalOffset = Math.min(verticalDiff * 0.2, 50) + offset;

    const cp1x = startX + HORIZONTAL_GAP * 0.4;
    const cp1y = startY + verticalOffset;
    const cp2x = endX - HORIZONTAL_GAP * 0.4;
    const cp2y = endY + verticalOffset;

    return {
      path: `M ${startX} ${startY} C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${endX} ${endY}`,
      cp1: { x: cp1x, y: cp1y },
      cp2: { x: cp2x, y: cp2y }
    };
  };

  // Generate curves for all sources
  const curves = sourcePositions.map((sourcePos, idx) => {
    // For compound connections, add slight vertical offset to prevent complete overlap
    const offset = isCompound ? (idx - (fromNodes.length - 1) / 2) * 5 : 0;
    return {
      ...generateCurvePath(CURVE_START_X, sourcePos.centerY, CURVE_END_X, targetCenterY, offset),
      sourceIdx: idx
    };
  });

  // Calculate bezier midpoint for attribution/rating positioning
  const bezierMidpoint = (start, cp1, cp2, end, t = 0.5) => {
    const x = Math.pow(1-t, 3)*start.x +
              3*Math.pow(1-t, 2)*t*cp1.x +
              3*(1-t)*Math.pow(t, 2)*cp2.x +
              Math.pow(t, 3)*end.x;
    const y = Math.pow(1-t, 3)*start.y +
              3*Math.pow(1-t, 2)*t*cp1.y +
              3*(1-t)*Math.pow(t, 2)*cp2.y +
              Math.pow(t, 3)*end.y;
    return {x, y};
  };

  // Use first curve for midpoint calculation (representative for compound)
  const firstCurve = curves[0];
  const midpoint = bezierMidpoint(
    { x: CURVE_START_X, y: sourceStackCenterY },
    firstCurve.cp1,
    firstCurve.cp2,
    { x: CURVE_END_X, y: targetCenterY }
  );

  return (
    <div className="connection-display-wrapper" style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: '20px',
      padding: '2rem',
      borderRadius: '15px',
      background: 'var(--modal-bg)',
      boxShadow: '12px 12px 24px var(--modal-shadow-1), -12px -12px 24px var(--modal-shadow-2)',
      ...containerStyle
    }}>
      <div className="connection-display-container" style={{
        width: `${CONTAINER_WIDTH}px`,
        height: `${CONTAINER_HEIGHT}px`,
        position: 'relative',
        background: 'transparent'
      }}>
      {/* Source nodes */}
      <div className="source-nodes">
        {sourcePositions.map((pos, idx) => (
          <div
            key={pos.node.id}
            className="source-node-wrapper"
            style={{
              position: 'absolute',
              left: `${pos.x}px`,
              top: `${pos.y}px`,
              width: `${NODE_DISPLAY_WIDTH}px`
            }}
          >
            <NodeDisplay
              nodeId={pos.node.id}
              nodeType={pos.node.type}
              content={pos.node.content}
              url={pos.node.url}
              contentStyle={{ maxWidth: '370px' }}
            />
          </div>
        ))}
      </div>

      {/* Target node */}
      <div
        className="target-node-wrapper"
        style={{
          position: 'absolute',
          left: `${TARGET_X}px`,
          top: `${targetY}px`,
          width: `${NODE_DISPLAY_WIDTH}px`
        }}
      >
        <NodeDisplay
          nodeId={toNode.id}
          nodeType={toNode.type}
          content={toNode.content}
          url={toNode.url}
          contentStyle={{ maxWidth: '370px' }}
        />
      </div>

      {/* SVG curves */}
      <svg
        className="connection-curves"
        width={CONTAINER_WIDTH}
        height={CONTAINER_HEIGHT}
        style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none', zIndex: 1 }}
      >
        {curves.map((curve, idx) => (
          <path
            key={idx}
            d={curve.path}
            stroke={curveColor}
            strokeWidth="2"
            fill="none"
            opacity="0.8"
            markerEnd="url(#arrowhead)"
          />
        ))}

        {/* Arrowhead marker */}
        <defs>
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="10"
            refX="9"
            refY="3"
            orient="auto"
            markerUnits="strokeWidth"
          >
            <path d="M0,0 L0,6 L9,3 z" fill={curveColor} />
          </marker>
        </defs>
      </svg>

      {/* Connection metadata overlay at midpoint */}
      <div
        className="connection-metadata"
        style={{
          position: 'absolute',
          left: `${midpoint.x}px`,
          top: `${midpoint.y}px`,
          transform: 'translate(-50%, -50%)',
          zIndex: 2
        }}
      >
        {/* UserAttribution above curve */}
        <div className="connection-attribution" style={{
          position: 'absolute',
          bottom: '40px',
          left: '50%',
          transform: 'translateX(-50%)',
          whiteSpace: 'nowrap'
        }}>
          <UserAttribution
            entityUuid={connectionId}
            entityType="connection"
            showTimestamp={true}
          />
        </div>

        {/* Logic type badge */}
        {logicType && (
          <div
            className="logic-badge"
            style={{
              position: 'absolute',
              top: '-15px',
              left: '50%',
              transform: 'translateX(-50%)',
              padding: '4px 12px',
              borderRadius: '12px',
              backgroundColor: curveColor,
              color: 'white',
              fontSize: '12px',
              fontWeight: 'bold',
              whiteSpace: 'nowrap'
            }}
          >
            {logicType}
          </div>
        )}

        {/* CommentsRating below curve */}
        <div className="connection-comments-rating" style={{
          position: 'absolute',
          top: '40px',
          left: '50%',
          transform: 'translateX(-50%)'
        }}>
          <CommentsRating
            entityUuid={connectionId}
            entityType="connection"
            tabsOnly={false}
            entityColor={curveColor}
            standalone={true}
          />
        </div>
      </div>
      </div>

      {/* Connection notes as caption */}
      {notes && (
        <div className="connection-notes" style={{
          width: `${CONTAINER_WIDTH}px`,
          fontSize: '14px',
          lineHeight: '1.6',
          color: 'var(--modal-text)',
          textAlign: 'center'
        }}>
          {notes}
        </div>
      )}
    </div>
  );
}
