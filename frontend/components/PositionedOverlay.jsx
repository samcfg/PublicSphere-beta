import { useState, useEffect } from 'react';

/**
 * Reusable overlay component that tracks Cytoscape element position
 * Automatically updates position on zoom, pan, and element movement
 * Scales with graph zoom level to maintain visual consistency
 *
 * @param {Object} props
 * @param {Object} props.cytoElement - Cytoscape element (node or edge) to track
 * @param {Object} props.cy - Cytoscape instance
 * @param {Function} props.getPosition - Optional function to compute position from element (defaults to renderedPosition for nodes, renderedMidpoint for edges)
 * @param {React.ReactNode} props.children - Content to render in overlay
 * @param {Object} props.offset - Optional {x, y} pixel offset from element position (scaled with zoom)
 */
export function PositionedOverlay({ cytoElement, cy, getPosition, children, offset = { x: 0, y: 0 } }) {
  const [position, setPosition] = useState(null);
  const [zoom, setZoom] = useState(1);

  useEffect(() => {
    if (!cytoElement || !cy) return;

    const updatePosition = () => {
      // Determine position based on element type
      let rendered;
      if (getPosition) {
        rendered = getPosition(cytoElement);
      } else {
        // Default: use renderedMidpoint for edges, renderedPosition for nodes
        rendered = cytoElement.isEdge?.()
          ? cytoElement.renderedMidpoint()
          : cytoElement.renderedPosition();
      }

      const containerRect = cy.container().getBoundingClientRect();
      const currentZoom = cy.zoom();

      setPosition({
        x: containerRect.left + rendered.x + offset.x * currentZoom,
        y: containerRect.top + rendered.y + offset.y * currentZoom
      });
      setZoom(currentZoom);
    };

    // Initial position
    updatePosition();

    // Track zoom and pan
    cy.on('zoom pan', updatePosition);

    // Track element movement (for draggable nodes)
    cytoElement.on('position', updatePosition);

    return () => {
      cy.off('zoom pan', updatePosition);
      cytoElement.off('position', updatePosition);
    };
  }, [cytoElement, cy, getPosition, offset.x, offset.y]);

  if (!position) return null;

  return (
    <div
      style={{
        position: 'absolute',
        left: `${position.x}px`,
        top: `${position.y}px`,
        transform: `scale(${zoom})`,
        transformOrigin: 'top left',
        zIndex: 1000,
        pointerEvents: 'auto'
      }}
    >
      {children}
    </div>
  );
}
