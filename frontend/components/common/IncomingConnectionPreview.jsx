import { NodeDisplay } from './NodeDisplay.jsx';
import { UserAttribution } from './UserAttribution.jsx';
import { CommentsRating } from './CommentsRating.jsx';
import '../../styles/components/ConnectionDisplay.css';

/**
 * IncomingConnectionPreview - Compact connection display without target node
 * Used in sidebar to show incoming connections to the current page's node
 *
 * @param {Object} props
 * @param {string} props.connectionId - Connection UUID
 * @param {Array<Object>} props.fromNodes - Source nodes [{id, content, type, url}, ...]
 * @param {string} props.logicType - 'AND'|'OR'|'NOT'|'NAND'
 * @param {string} props.notes - Optional connection notes
 * @param {Function} props.onClick - Optional click handler to navigate to full connection view
 */
export function IncomingConnectionPreview({
  connectionId,
  fromNodes,
  logicType,
  notes,
  onClick
}) {
  // Determine if connection is negative
  const isNegative = logicType === 'NOT' || logicType === 'NAND';
  const curveColor = isNegative
    ? getComputedStyle(document.documentElement).getPropertyValue('--accent-red').trim() || '#e74c3c'
    : getComputedStyle(document.documentElement).getPropertyValue('--accent-green').trim() || '#68d391';

  const isCompound = fromNodes.length > 1;

  // Layout constants - scaled down from ConnectionDisplay
  const CONTAINER_WIDTH = 500;
  const CONTAINER_HEIGHT = isCompound ? 400 + (fromNodes.length - 1) * 150 : 300;
  const NODE_DISPLAY_WIDTH = 300;
  const SOURCE_X = 20;
  const CURVE_START_X = SOURCE_X + NODE_DISPLAY_WIDTH;
  const CURVE_END_X = CONTAINER_WIDTH - 40; // End near right edge
  const HORIZONTAL_GAP = CURVE_END_X - CURVE_START_X;

  // Calculate source node positions
  const sourcePositions = [];
  if (isCompound) {
    const stackHeight = fromNodes.length * 150 + (fromNodes.length - 1) * 20;
    const startY = (CONTAINER_HEIGHT - stackHeight) / 2 + 75;
    fromNodes.forEach((node, idx) => {
      sourcePositions.push({
        node,
        x: SOURCE_X,
        y: startY + idx * 170,
        centerY: startY + idx * 170 + 75
      });
    });
  } else {
    sourcePositions.push({
      node: fromNodes[0],
      x: SOURCE_X,
      y: CONTAINER_HEIGHT / 2 - 75,
      centerY: CONTAINER_HEIGHT / 2
    });
  }

  // Calculate source stack center (for curve convergence)
  const sourceStackCenterY = sourcePositions.reduce((sum, pos) => sum + pos.centerY, 0) / sourcePositions.length;

  // Target point (right edge, centered vertically on source stack)
  const targetY = sourceStackCenterY;

  // Bezier curve calculation
  const generateCurvePath = (startX, startY, endX, endY, offset = 0) => {
    const verticalDiff = Math.abs(endY - startY);
    const verticalOffset = Math.min(verticalDiff * 0.2, 30) + offset;

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
    const offset = isCompound ? (idx - (fromNodes.length - 1) / 2) * 3 : 0;
    return {
      ...generateCurvePath(CURVE_START_X, sourcePos.centerY, CURVE_END_X, targetY, offset),
      sourceIdx: idx
    };
  });

  // Calculate bezier midpoint for attribution positioning
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

  const firstCurve = curves[0];
  const midpoint = bezierMidpoint(
    { x: CURVE_START_X, y: sourceStackCenterY },
    firstCurve.cp1,
    firstCurve.cp2,
    { x: CURVE_END_X, y: targetY }
  );

  return (
    <div
      className="incoming-connection-preview"
      onClick={onClick}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        padding: '1.5rem',
        borderRadius: '12px',
        background: 'var(--modal-bg)',
        boxShadow: '8px 8px 16px var(--modal-shadow-1), -8px -8px 16px var(--modal-shadow-2)',
        cursor: onClick ? 'pointer' : 'default'
      }}
    >
      <div
        className="connection-preview-container"
        style={{
          width: `${CONTAINER_WIDTH}px`,
          height: `${CONTAINER_HEIGHT}px`,
          position: 'relative',
          background: 'transparent'
        }}
      >
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
                contentStyle={{ maxWidth: '270px', fontSize: '13px' }}
              />
            </div>
          ))}
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
              opacity="0.7"
              markerEnd="url(#arrowhead-preview)"
            />
          ))}

          {/* Arrowhead marker */}
          <defs>
            <marker
              id="arrowhead-preview"
              markerWidth="8"
              markerHeight="8"
              refX="7"
              refY="3"
              orient="auto"
              markerUnits="strokeWidth"
            >
              <path d="M0,0 L0,6 L7,3 z" fill={curveColor} />
            </marker>
          </defs>
        </svg>

        {/* Connection metadata overlay at curve end */}
        <div
          className="connection-metadata"
          style={{
            position: 'absolute',
            left: `${CURVE_END_X}px`,
            top: `${targetY}px`,
            transform: 'translate(-50%, -50%)',
            zIndex: 2
          }}
        >
          {/* Logic type badge at curve end */}
          {logicType && (
            <div
              className="logic-badge"
              style={{
                position: 'absolute',
                top: '-12px',
                left: '50%',
                transform: 'translateX(-50%)',
                padding: '3px 10px',
                borderRadius: '10px',
                backgroundColor: curveColor,
                color: 'white',
                fontSize: '11px',
                fontWeight: 'bold',
                whiteSpace: 'nowrap'
              }}
            >
              {logicType}
            </div>
          )}

          {/* UserAttribution below logic badge */}
          <div className="connection-attribution" style={{
            position: 'absolute',
            top: '20px',
            left: '50%',
            transform: 'translateX(-50%)',
            whiteSpace: 'nowrap',
            fontSize: '11px'
          }}>
            <UserAttribution
              entityUuid={connectionId}
              entityType="connection"
              showTimestamp={false}
            />
          </div>
        </div>
      </div>

      {/* Connection notes as caption */}
      {notes && (
        <div className="connection-notes" style={{
          width: `${CONTAINER_WIDTH}px`,
          fontSize: '12px',
          lineHeight: '1.5',
          color: 'var(--modal-text)',
          textAlign: 'center',
          marginTop: '10px'
        }}>
          {notes}
        </div>
      )}
    </div>
  );
}
