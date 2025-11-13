import { useRef, useEffect, forwardRef, useImperativeHandle, useState } from 'react';
import cytoscape from 'cytoscape';
import cytoscapeDagre from 'cytoscape-dagre';
import { PositionedOverlay } from './PositionedOverlay.jsx';

// Register dagre layout extension
cytoscape.use(cytoscapeDagre);

/**
 * Graph visualization component using Cytoscape.js
 * Renders interactive node-edge graph with hierarchical layout
 * Exposes resetView() and fitToScreen() methods via ref
 *
 * @param {Object} props
 * @param {Object} props.data - Cytoscape elements: {elements: [{data: {...}}, ...]}
 * @param {React.Ref} ref - Forward ref for imperative method access
 */
export const Graph = forwardRef(({ data }, ref) => {
  const containerRef = useRef(null); // DOM container for Cytoscape
  const cyRef = useRef(null); // Cytoscape instance
  const [activeEdgeTooltip, setActiveEdgeTooltip] = useState(null); // {edge: cytoscapeEdge, notes: string}

  // Expose methods to parent component via ref
  useImperativeHandle(ref, () => ({
    resetView: () => {
      if (cyRef.current) {
        cyRef.current.zoom(1);
        cyRef.current.center();
      }
    },
    fitToScreen: () => {
      if (cyRef.current) {
        cyRef.current.fit();
      }
    }
  }));

  // Helper to read CSS variables
  const getColors = () => {
    const rootStyles = getComputedStyle(document.documentElement);
    return {
      bgPrimary: rootStyles.getPropertyValue('--bg-primary').trim(),
      textPrimary: rootStyles.getPropertyValue('--text-primary').trim(),
      textSecondary: rootStyles.getPropertyValue('--text-secondary').trim(),
      accentGreen: rootStyles.getPropertyValue('--accent-green').trim(),
      accentBlue: rootStyles.getPropertyValue('--accent-blue').trim(),
      accentBlueDark: rootStyles.getPropertyValue('--accent-blue-dark').trim(),
      nodeDefault: rootStyles.getPropertyValue('--node-default').trim(),
      nodeSource: rootStyles.getPropertyValue('--node-source').trim(),
      nodeText: rootStyles.getPropertyValue('--node-text').trim()
    };
  };

  // Initialize Cytoscape instance
  useEffect(() => {
    if (!containerRef.current) return;

    const colors = getColors();

    // Extract first font from CSS variable (Cytoscape doesn't support font stacks)
    const rootStyles = getComputedStyle(document.documentElement);
    const fontFamilyVar = rootStyles.getPropertyValue('--font-family-base').trim();
    const fontFamily = fontFamilyVar.split(',')[0].replace(/['"]/g, '').trim();

    // Create Cytoscape instance
    cyRef.current = cytoscape({
      container: containerRef.current,
      wheelSensitivity: 0.25,

      style: [
        {
          selector: 'node',
          style: {
            'background-color': colors.nodeDefault,
            'label': 'data(content)',
            'color': colors.nodeText,
            'text-valign': 'center',
            'text-halign': 'center',
            'font-family': fontFamily,
            'font-size': '12px',
            'font-weight': 'bold',
            'text-wrap': 'wrap',
            'text-max-width': '200px',
            'width': 'label',
            'height': 'label',
            'min-width': '80px',
            'min-height': '40px',
            'padding': '10px',
            'shape': 'round-rectangle',
            'border-width': 1,
            'border-color': colors.accentBlue
          }
        },
        {
          selector: 'node[label = "Source"]',
          style: {
            'border-color': colors.accentGreen
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 3,
            'line-color': colors.accentGreen,
            'target-arrow-color': colors.accentGreen,
            'target-arrow-shape': 'triangle',
            'arrow-scale': 1.2,
            'curve-style': 'bezier'
          }
        },
        {
          selector: 'edge[logic_type = "NOT"], edge[logic_type = "NAND"]',
          style: {
            'line-color': '#e74c3c',
            'target-arrow-color': '#e74c3c'
          }
        },
        {
          selector: 'edge.highlighted',
          style: {
            'width': 5,
            'line-color': '#ffffff',
            'target-arrow-color': '#ffffff'
          }
        },
        {
          selector: 'node.hovered',
          style: {
            'overlay-color': colors.accentBlue,
            'overlay-opacity': 0.3,
            'overlay-padding': 8,
            'transition-property': 'overlay-opacity, overlay-padding',
            'transition-duration': '0.2s',
            'transition-timing-function': 'ease-out'
          }
        },
        {
          selector: 'node[label = "Source"].hovered',
          style: {
            'overlay-color': colors.accentGreen
          }
        }
      ]
    });

    // Setup interaction handlers
    const cleanupEdgeTooltip = setupEdgeTooltip(cyRef.current, setActiveEdgeTooltip);
    setupCompoundEdgeHighlighting(cyRef.current);
    setupNodeHover(cyRef.current);
    setupBundlingRecalculation(cyRef.current);
    setupBackgroundSync(cyRef.current);

    // Cleanup on unmount
    return () => {
      cleanupEdgeTooltip?.();
      if (cyRef.current) {
        cyRef.current.destroy();
      }
    };
  }, []); // Run once on mount

  // Update graph when data changes
  useEffect(() => {
    if (!cyRef.current || !data) return;

    // Clear existing elements
    cyRef.current.elements().remove();

    // Add new elements
    if (data.elements && data.elements.length > 0) {
      cyRef.current.add(data.elements);
      applyLayout(cyRef.current, 'dagre');
    }
  }, [data]); // Re-run when data changes

  // Listen for theme changes and update node colors
  useEffect(() => {
    if (!cyRef.current) return;

    const updateTheme = () => {
      const colors = getColors();

      cyRef.current.style()
        .selector('node')
        .style({
          'background-color': colors.nodeDefault,
          'color': colors.nodeText
        })
        .selector('node[label = "Source"]')
        .style({
          'background-color': colors.nodeSource
        })
        .update();
    };

    // Watch for data-theme attribute changes on <html>
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'attributes' && mutation.attributeName === 'data-theme') {
          updateTheme();
        }
      });
    });

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme']
    });

    return () => observer.disconnect();
  }, []); // Run once on mount

  return (
    <>
      <div
        ref={containerRef}
        style={{ width: '100%', height: '100vh' }}
        id="cy-container"
      />

      {activeEdgeTooltip && cyRef.current && (
        <PositionedOverlay
          cytoElement={activeEdgeTooltip.edge}
          cy={cyRef.current}
          offset={{ x: 20, y: -10 }}
        >
          <div className="edge-tooltip">
            <div className="tooltip-content">
              {activeEdgeTooltip.notes}
            </div>
          </div>
        </PositionedOverlay>
      )}
    </>
  );
});

// ============================================================================
// Helper Functions (moved outside component to avoid recreation on each render)
// ============================================================================

function setupEdgeTooltip(cy, setActiveEdgeTooltip) {
  // Click on edge to show tooltip
  cy.on('tap', 'edge', (event) => {
    const edge = event.target;
    const notes = edge.data('notes') || 'No notes available';

    setActiveEdgeTooltip({ edge, notes });

    event.stopPropagation();
    event.preventDefault();
  });

  // Click on cytoscape background to hide tooltip
  cy.on('tap', (event) => {
    if (event.target === cy) {
      setActiveEdgeTooltip(null);
    }
  });

  // Click outside graph to hide tooltip
  const hideTooltip = (event) => {
    const container = cy.container();
    if (!container.contains(event.target)) {
      setActiveEdgeTooltip(null);
    }
  };

  document.addEventListener('click', hideTooltip);

  // Return cleanup function
  return () => {
    document.removeEventListener('click', hideTooltip);
  };
}

function setupCompoundEdgeHighlighting(cy) {
  /**
   * Highlight all edges in a compound group when hovering over any one edge
   * Edges are grouped by composite_id
   */
  cy.on('mouseover', 'edge', (event) => {
    const edge = event.target;
    const compositeId = edge.data('composite_id');

    if (compositeId) {
      const compoundEdges = cy.edges().filter(e =>
        e.data('composite_id') === compositeId
      );
      compoundEdges.addClass('highlighted');
    } else {
      edge.addClass('highlighted');
    }
  });

  cy.on('mouseout', 'edge', (event) => {
    const edge = event.target;
    const compositeId = edge.data('composite_id');

    if (compositeId) {
      const compoundEdges = cy.edges().filter(e =>
        e.data('composite_id') === compositeId
      );
      compoundEdges.removeClass('highlighted');
    } else {
      edge.removeClass('highlighted');
    }
  });
}

function setupNodeHover(cy) {
  /**
   * Add hover effect to nodes using addClass/removeClass pattern
   * Provides smooth overlay glow on hover with automatic transitions
   */
  cy.on('mouseover', 'node', (event) => {
    const node = event.target;
    node.addClass('hovered');
  });

  cy.on('mouseout', 'node', (event) => {
    const node = event.target;
    node.removeClass('hovered');
  });
}

function setupBundlingRecalculation(cy) {
  /**
   * Recalculate compound edge bundling when nodes are repositioned
   * Triggers on 'free' event (when user releases dragged node)
   */
  cy.on('free', 'node', () => {
    applyCompoundEdgeBundling(cy);
  });
}

function setupBackgroundSync(cy) {
  /**
   * Sync background grid with pan/zoom transformations
   */
  function updateBackground() {
    const zoom = cy.zoom();
    const pan = cy.pan();
    const container = cy.container();

    // Calculate grid size scaled by zoom
    const gridSize = 20 * zoom;

    // Calculate background position offset by pan
    const bgX = pan.x % gridSize;
    const bgY = pan.y % gridSize;

    container.style.backgroundSize = `${gridSize}px ${gridSize}px`;
    container.style.backgroundPosition = `${bgX}px ${bgY}px`;
  }

  // Update on pan and zoom events
  cy.on('pan zoom', updateBackground);

  // Initial update
  updateBackground();
}

function applyLayout(cy, layoutName = 'dagre') {
  const layoutOptions = layoutName === 'dagre' ? {
    name: 'dagre',
    rankDir: 'BT',           // Bottom-to-Top: premises below, conclusions above
    nodeSep: 80,             // Horizontal spacing between nodes at same rank
    rankSep: 120,            // Vertical spacing between ranks
    animate: false
  } : {
    name: layoutName,
    animate: false
  };

  const layout = cy.layout(layoutOptions);

  layout.on('layoutstop', () => {
    // After layout completes, apply compound edge bundling
    applyCompoundEdgeBundling(cy);
  });

  layout.run();
}

function applyCompoundEdgeBundling(cy) {
  /**
   * Apply bundled bezier curves to edges with shared composite_id
   */
  const edges = cy.edges();
  const compoundGroups = identifyCompoundEdgeGroups(edges);

  compoundGroups.forEach((edgeGroup) => {
    if (edgeGroup.length < 2) {
      return; // Single edge, no bundling needed
    }

    // All edges in group share same target (by design of compound edges)
    const targetNode = cy.getElementById(edgeGroup[0].data('target'));
    const controlPoints = calculateBundlingControlPoints(cy, edgeGroup, targetNode);

    // Apply relative control points to each edge
    controlPoints.forEach(({ edge, weight, distance }) => {
      edge.style({
        'curve-style': 'unbundled-bezier',
        'control-point-distances': [distance],
        'control-point-weights': [weight]
      });
    });
  });
}

function identifyCompoundEdgeGroups(edges) {
  /**
   * Groups edges by composite_id for bundling visualization
   * Returns: Map<composite_id, Array<edge>>
   */
  const groups = new Map();

  edges.forEach(edge => {
    const compositeId = edge.data('composite_id');
    if (compositeId) {
      if (!groups.has(compositeId)) {
        groups.set(compositeId, []);
      }
      groups.get(compositeId).push(edge);
    }
  });

  return groups;
}

function calculateBundlingControlPoints(cy, edgeGroup, targetNode) {
  /**
   * Calculate bezier control points for compound edges to converge near target
   *
   * Strategy:
   * 1. Get positions of all source nodes and target
   * 2. Calculate convergence point (shared absolute position near target)
   * 3. For each edge, convert convergence point to relative control point
   */
  const targetPos = targetNode.position();
  const sourcePositions = edgeGroup.map(edge => {
    const sourceNode = cy.getElementById(edge.data('source'));
    return sourceNode.position();
  });

  // Calculate centroid of source nodes
  const centroid = {
    x: sourcePositions.reduce((sum, pos) => sum + pos.x, 0) / sourcePositions.length,
    y: sourcePositions.reduce((sum, pos) => sum + pos.y, 0) / sourcePositions.length
  };

  // Convergence point: 30% from target toward centroid
  const convergenceRatio = 0.7;
  const convergencePoint = {
    x: targetPos.x + (centroid.x - targetPos.x) * convergenceRatio,
    y: targetPos.y + (centroid.y - targetPos.y) * convergenceRatio
  };

  // Convert to relative control points for each edge
  return edgeGroup.map((edge, index) => {
    const sourcePos = sourcePositions[index];

    // Vector from source to target
    const dx = targetPos.x - sourcePos.x;
    const dy = targetPos.y - sourcePos.y;
    const edgeLength = Math.sqrt(dx * dx + dy * dy);

    if (edgeLength === 0) {
      return { edge, weight: 0.5, distance: 0 };
    }

    // Normalized direction vector
    const nx = dx / edgeLength;
    const ny = dy / edgeLength;

    // Vector from source to convergence point
    const cpx = convergencePoint.x - sourcePos.x;
    const cpy = convergencePoint.y - sourcePos.y;

    // Project convergence point onto source-target line to get weight
    const projection = (cpx * dx + cpy * dy) / (edgeLength * edgeLength);
    const weight = Math.max(0, Math.min(1, projection));

    // Point on line at weight position
    const pointOnLineX = sourcePos.x + dx * weight;
    const pointOnLineY = sourcePos.y + dy * weight;

    // Perpendicular distance from line to convergence point
    const distX = convergencePoint.x - pointOnLineX;
    const distY = convergencePoint.y - pointOnLineY;

    // Perpendicular vector to edge (rotated 90°)
    const perpX = -ny;
    const perpY = nx;

    const distance = distX * perpX + distY * perpY;

    return { edge, weight, distance };
  });
}
