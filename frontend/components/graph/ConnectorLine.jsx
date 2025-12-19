/**
 * ConnectorLine - Animated connection line component
 *
 * Renders a dashed, subtly curved line with a shining animation effect.
 * Used to connect UI elements in the NodeCreationModal triangle layout.
 *
 * @param {Object} props
 * @param {number} props.x1 - Start X coordinate
 * @param {number} props.y1 - Start Y coordinate
 * @param {number} props.x2 - End X coordinate
 * @param {number} props.y2 - End Y coordinate
 * @param {string} props.color - Stroke color (CSS variable or hex)
 * @param {boolean} props.showArrow - Whether to show arrow marker at endpoint
 */
export function ConnectorLine({ x1, y1, x2, y2, color, showArrow = false }) {
  // Calculate control points for S-curve
  // True S-shape: curves one direction, then reverses to other direction
  const dx = x2 - x1;
  const dy = y2 - y1;
  const distance = Math.sqrt(dx * dx + dy * dy);

  // Perpendicular offset for curve (8% of distance for pronounced S)
  const curveMagnitude = distance * 0.08;

  // Perpendicular vector (normalized)
  const perpX = -dy / distance;
  const perpY = dx / distance;

  // S-curve control points:
  // First control point: 1/3 along line, offset in +perpendicular direction
  // Second control point: 2/3 along line, offset in -perpendicular direction
  // This creates the characteristic S-shape
  const cp1X = x1 + dx * 0.33 + perpX * curveMagnitude;
  const cp1Y = y1 + dy * 0.33 + perpY * curveMagnitude;
  const cp2X = x1 + dx * 0.67 - perpX * curveMagnitude;
  const cp2Y = y1 + dy * 0.67 - perpY * curveMagnitude;

  // SVG path: cubic Bezier curve
  const pathData = `M ${x1},${y1} C ${cp1X},${cp1Y} ${cp2X},${cp2Y} ${x2},${y2}`;

  // Unique ID for this line's gradient
  const gradientId = `shine-gradient-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <g>
      {/* Base dashed path */}
      <path
        d={pathData}
        stroke={color}
        strokeWidth={2}
        strokeDasharray="8 4"
        strokeLinecap="round"
        fill="none"
        opacity={0.6}
      />

      {/* Animated shine overlay */}
      <path
        d={pathData}
        stroke={`url(#${gradientId})`}
        strokeWidth={2}
        strokeDasharray="8 4"
        strokeLinecap="round"
        fill="none"
        opacity={0.8}
        style={{
          animation: 'shine-sweep 2s ease-in-out infinite'
        }}
      />

      {/* Arrow marker at endpoint */}
      {showArrow && (
        <defs>
          <marker
            id={`arrow-${gradientId}`}
            markerWidth="10"
            markerHeight="10"
            refX="9"
            refY="3"
            orient="auto"
            markerUnits="strokeWidth"
          >
            <polygon
              points="0 0, 10 3, 0 6"
              fill={color}
              opacity={0.8}
            />
          </marker>
        </defs>
      )}

      {/* Shine gradient definition */}
      <defs>
        <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor={color} stopOpacity={0} />
          <stop offset="50%" stopColor="#ffffff" stopOpacity={0.9} />
          <stop offset="100%" stopColor={color} stopOpacity={0} />
          <animateTransform
            attributeName="gradientTransform"
            type="translate"
            from="-1 0"
            to="1 0"
            dur="2s"
            repeatCount="indefinite"
          />
        </linearGradient>
      </defs>
    </g>
  );
}
