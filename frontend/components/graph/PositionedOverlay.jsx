import { useRef, useEffect } from 'react';

/**
 * Reusable overlay component that tracks Cytoscape element position
 * Automatically updates position on zoom, pan, and element movement
 * Scales with graph zoom level to maintain visual consistency
 * Uses direct DOM manipulation for smooth 60fps tracking
 *
 * @param {Object} props
 * @param {Object} props.cytoElement - Cytoscape element (node or edge) to track
 * @param {Object} props.cy - Cytoscape instance
 * @param {Function} props.getPosition - Optional function to compute position from element (defaults to renderedPosition for nodes, renderedMidpoint for edges)
 * @param {React.ReactNode} props.children - Content to render in overlay
 * @param {Object} props.offset - Optional {x, y} pixel offset from element position (scaled with zoom)
 * @param {boolean} props.passThrough - If true, wrapper has pointerEvents: none (default false)
 */
export function PositionedOverlay({ cytoElement, cy, getPosition, children, offset = { x: 0, y: 0 }, passThrough = false }) {
  const overlayRef = useRef(null);

  useEffect(() => {
    if (!cytoElement || !cy || !overlayRef.current) return;

    const offsetX = offset.x;
    const offsetY = offset.y;

    const updatePosition = () => {
      if (!overlayRef.current) return;

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

      const x = containerRect.left + rendered.x + offsetX * currentZoom;
      const y = containerRect.top + rendered.y + offsetY * currentZoom;

      // Direct DOM manipulation - no React re-render
      overlayRef.current.style.left = `${x}px`;
      overlayRef.current.style.top = `${y}px`;
      overlayRef.current.style.transform = `scale(${currentZoom})`;
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

  return (
    <div
      ref={overlayRef}
      style={{
        position: 'absolute',
        left: 0,
        top: 0,
        transform: 'scale(1)',
        transformOrigin: 'top left',
        zIndex: 1000,
        pointerEvents: passThrough ? 'none' : 'auto'
      }}
    >
      {children}
    </div>
  );
}
