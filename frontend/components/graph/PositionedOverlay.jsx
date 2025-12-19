import { useRef, useEffect } from 'react';

/**
 * Reusable overlay component that tracks either Cytoscape element OR DOM element position
 *
 * Cytoscape mode:
 * - Tracks graph element (node/edge) position in rendered coordinates
 * - Updates on zoom, pan, and element movement
 * - Scales with graph zoom level
 *
 * DOM mode:
 * - Tracks arbitrary DOM element position (via ref)
 * - Updates on resize, scroll, zoom, pan
 * - Maintains zoom scaling for visual consistency
 * - Enables dynamic offset calculation based on element dimensions
 *
 * Uses direct DOM manipulation for smooth 60fps tracking
 *
 * @param {Object} props
 * @param {Object} props.cytoElement - Cytoscape element (node or edge) to track (Cytoscape mode)
 * @param {Object} props.domElement - React ref to DOM element to track (DOM mode)
 * @param {Object} props.cy - Cytoscape instance (required for both modes for zoom/pan tracking)
 * @param {Function} props.getPosition - Optional function to compute position from cytoElement (Cytoscape mode only)
 * @param {Object} props.offset - Static {x, y} pixel offset (scaled with zoom)
 * @param {Function} props.getOffset - Dynamic offset calculator: (rect) => {x, y} (DOM mode only, takes precedence over offset)
 * @param {React.ReactNode} props.children - Content to render in overlay
 * @param {boolean} props.passThrough - If true, wrapper has pointerEvents: none (default false)
 */
export function PositionedOverlay({ cytoElement, domElement, cy, getPosition, children, offset = { x: 0, y: 0 }, getOffset, passThrough = false }) {
  const overlayRef = useRef(null);

  useEffect(() => {
    if (!overlayRef.current || !cy) return;

    // CYTOSCAPE MODE: Track graph element position
    if (cytoElement) {
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
    }

    // DOM MODE: Track DOM element position
    if (domElement?.current) {
      const updatePosition = () => {
        if (!overlayRef.current || !domElement.current) return;

        const rect = domElement.current.getBoundingClientRect();
        const currentZoom = cy.zoom();

        // Convert rect from screen (zoomed) coordinates to logical coordinates
        const logicalRect = {
          left: rect.left,
          top: rect.top,
          width: rect.width / currentZoom,
          height: rect.height / currentZoom,
          right: rect.right,
          bottom: rect.bottom
        };

        // Calculate offset in logical coordinate space
        const calculatedOffset = getOffset ? getOffset(logicalRect) : offset;

        // Apply offset in logical space, then scale will convert to screen space
        const x = rect.left + calculatedOffset.x * currentZoom;
        const y = rect.top + calculatedOffset.y * currentZoom;

        overlayRef.current.style.left = `${x}px`;
        overlayRef.current.style.top = `${y}px`;
        overlayRef.current.style.transform = `scale(${currentZoom})`;
      };

      // Initial position
      updatePosition();

      // Track DOM element resize
      const resizeObserver = new ResizeObserver(updatePosition);
      resizeObserver.observe(domElement.current);

      // Track Cytoscape zoom and pan (affects final screen position)
      cy.on('zoom pan', updatePosition);

      // Track window resize and scroll
      window.addEventListener('resize', updatePosition);
      window.addEventListener('scroll', updatePosition, true);

      return () => {
        resizeObserver.disconnect();
        cy.off('zoom pan', updatePosition);
        window.removeEventListener('resize', updatePosition);
        window.removeEventListener('scroll', updatePosition, true);
      };
    }
  }, [cytoElement, domElement, cy, getPosition, offset, getOffset]);

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
