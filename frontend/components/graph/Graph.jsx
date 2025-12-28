import { useRef, useEffect, forwardRef, useImperativeHandle, useState } from 'react';
import cytoscape from 'cytoscape';
import cytoscapeDagre from 'cytoscape-dagre';
import { OnClickEdge, setupEdgeTooltip } from './OnClickEdge.jsx';
import { OnClickNode, setupNodeTooltip } from './OnClickNode.jsx';
import { styleVariants } from './graphStyles1.js';

// Register dagre layout extension
cytoscape.use(cytoscapeDagre);

/**
 * Graph visualization component using Cytoscape.js
 * Renders interactive node-edge graph with hierarchical layout
 * Exposes resetView() and fitToScreen() methods via ref
 *
 * @param {Object} props
 * @param {Object} props.data - Cytoscape elements: {elements: [{data: {...}}, ...]}
 * @param {Function} props.updateAttributions - Function to update attribution cache locally
 * @param {Function} props.onGraphChange - Fallback refetch function for complex updates
 * @param {React.Ref} ref - Forward ref for imperative method access
 */
export const Graph = forwardRef(({ data, updateAttributions, onGraphChange, contextNodeId }, ref) => {
  const containerRef = useRef(null); // DOM container for Cytoscape
  const cyRef = useRef(null); // Cytoscape instance
  const [activeEdgeTooltip, setActiveEdgeTooltip] = useState(null); // {edge: cytoscapeEdge, clickOffset: {x, y}}
  const [activeNodeTooltip, setActiveNodeTooltip] = useState(null); // {node: cytoscapeNode, clickOffset: {x, y}}

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
      wheelSensitivity: 0.1,
      style: styleVariants.refined(colors, fontFamily)
    });

    // Setup interaction handlers
    const cleanupEdgeTooltip = setupEdgeTooltip(cyRef.current, setActiveEdgeTooltip);
    const cleanupNodeTooltip = setupNodeTooltip(cyRef.current, setActiveNodeTooltip, contextNodeId);
    setupCompoundEdgeHighlighting(cyRef.current);
    setupNodeHover(cyRef.current);
    setupBundlingRecalculation(cyRef.current);
    setupBackgroundSync(cyRef.current);

    // Cleanup on unmount
    return () => {
      cleanupEdgeTooltip?.();
      cleanupNodeTooltip?.();
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
      applyLayout(cyRef.current, 'dagre', contextNodeId);
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
          'color': colors.nodeText,
          'border-color': colors.accentBlue
        })
        .selector('node[label = "Source"]')
        .style({
          'background-color': colors.nodeSource,
          'border-color': colors.accentBlueDark
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

      <OnClickEdge
        key={activeEdgeTooltip?.edge?.id()}
        activeEdgeTooltip={activeEdgeTooltip}
        cy={cyRef.current}
      />

      <OnClickNode
        key={activeNodeTooltip?.node?.id()}
        activeNodeTooltip={activeNodeTooltip}
        cy={cyRef.current}
        updateAttributions={updateAttributions}
        onGraphChange={onGraphChange}
        onClose={() => setActiveNodeTooltip(null)}
      />
    </>
  );
});

// ============================================================================
// Helper Functions (moved outside component to avoid recreation on each render)
// ============================================================================

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

function applyLayout(cy, layoutName = 'dagre', contextNodeId = null) {
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

    // Apply context node styling if contextNodeId is provided
    if (contextNodeId) {
      const contextNode = cy.getElementById(contextNodeId);
      if (contextNode.length > 0) {
        contextNode.addClass('context-node');

        // Find and style immediate neighbors
        const connectedEdges = contextNode.connectedEdges();
        const neighbors = connectedEdges.connectedNodes().filter(n => n.id() !== contextNodeId);
        neighbors.addClass('context-neighbor');
      }
    }

    // Set initial zoom and center on context node
    // Initial zoom bounds - prevents extreme zoom levels on page load
    const MIN_INITIAL_ZOOM = 0.3;
    const MAX_INITIAL_ZOOM = 2.0;
    const TARGET_CONTEXT_NODE_WIDTH = 600; // Target rendered width in pixels
    const CONTEXT_NODE_MIN_WIDTH = 300; // From graphStyles1.js context-node min-width

    let initialZoom = 1.0; // Default if no context node

    if (contextNodeId) {
      const contextNode = cy.getElementById(contextNodeId);
      if (contextNode.length > 0) {
        // Calculate zoom to make context node appear ~600px wide
        // At zoom=1, min-width is 300px. At zoom=2, it's 600px.
        initialZoom = TARGET_CONTEXT_NODE_WIDTH / CONTEXT_NODE_MIN_WIDTH;

        // Clamp to reasonable bounds
        initialZoom = Math.max(MIN_INITIAL_ZOOM, Math.min(MAX_INITIAL_ZOOM, initialZoom));

        // Set zoom and center on context node
        cy.zoom(initialZoom);
        cy.center(contextNode);
      } else {
        // Context node ID provided but not found, use default
        cy.zoom(initialZoom);
        cy.center();
      }
    } else {
      // No context node specified, use default
      cy.zoom(initialZoom);
      cy.center();
    }
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
