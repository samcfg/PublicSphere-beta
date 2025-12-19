/**
 * Cytoscape.js Capabilities Demo
 *
 * This file demonstrates:
 * 1. Dynamic edge width based on rating data
 * 2. Animated border effects for nodes
 *
 * Use these examples to integrate into your graphStyles1.js
 */

// ============================================================================
// 1. DYNAMIC EDGE WIDTH BASED ON RATING
// ============================================================================

/**
 * Edge width can be data-driven using mapData function
 * Maps a data field to a continuous style property
 *
 * Assumes your edge data has a 'rating' field (0-100 scale)
 * If you want to use aggregated ratings, you'd need to:
 * - Fetch ratings from /api/social/ratings/ for each connection
 * - Attach avg_score to edge.data() dynamically after loading graph
 */

export const edgeWidthByRating = {
  selector: 'edge',
  style: {
    // Map rating (0-100) to width (1-10 pixels)
    'width': 'mapData(rating, 0, 100, 1, 10)',

    // Alternative: Discrete bins instead of continuous
    // 'width': function(ele) {
    //   const rating = ele.data('rating') || 0;
    //   if (rating >= 80) return 8;
    //   if (rating >= 60) return 6;
    //   if (rating >= 40) return 4;
    //   if (rating >= 20) return 2;
    //   return 1;
    // },

    'line-color': '#68d391',
    'target-arrow-color': '#68d391',
    'target-arrow-shape': 'triangle'
  }
};

/**
 * Example usage in refined style variant:
 * Replace the basic edge selector with this:
 */
export const edgeStyleWithRating = (colors) => [
  {
    selector: 'edge',
    style: {
      'width': 'mapData(rating, 0, 100, 1, 10)',
      'line-color': colors.accentGreen,
      'target-arrow-color': colors.accentGreen,
      'target-arrow-shape': 'triangle',
      'arrow-scale': 1,
      'curve-style': 'straight'
    }
  }
];

/**
 * To attach rating data to edges after graph loads:
 */
export async function enrichEdgesWithRatings(cy, apiClient) {
  const edges = cy.edges();

  // Fetch ratings for all connections in parallel
  const ratingPromises = edges.map(async (edge) => {
    const connectionId = edge.data('id');
    try {
      const response = await apiClient.getRatings({
        entity: connectionId,
        dimension: 'confidence' // or 'relevance'
      });
      return {
        edge,
        rating: response.data?.avg_score || 0 // Default to 0 if no ratings
      };
    } catch (err) {
      console.warn(`Failed to fetch rating for ${connectionId}:`, err);
      return { edge, rating: 0 };
    }
  });

  const results = await Promise.all(ratingPromises);

  // Attach rating to each edge's data
  results.forEach(({ edge, rating }) => {
    edge.data('rating', rating);
  });

  // Force style recalculation
  cy.style().update();
}


// ============================================================================
// 2. ANIMATED BORDERS FOR NODES
// ============================================================================

/**
 * Cytoscape supports CSS-like animations via transition properties
 * For more complex animations, use keyframe-like state changes
 */

// Basic pulsing border animation (smooth transition)
export const pulsingBorderStyle = {
  selector: 'node.pulsing',
  style: {
    'border-width': 4,
    'border-color': '#3498db',
    'border-opacity': 0.8,
    'transition-property': 'border-width, border-opacity',
    'transition-duration': '1s',
    'transition-timing-function': 'ease-in-out'
  }
};

/**
 * To create continuous pulsing effect:
 * Alternate between two states using JavaScript interval
 */
export function startPulsingAnimation(cy, nodeSelector = 'node.highlight') {
  const nodes = cy.$(nodeSelector);
  let phase = 0;

  const interval = setInterval(() => {
    phase = (phase + 1) % 2;

    nodes.style({
      'border-width': phase === 0 ? 2 : 6,
      'border-opacity': phase === 0 ? 0.6 : 1.0
    });
  }, 1000); // Toggle every 1 second

  // Return cleanup function
  return () => clearInterval(interval);
}

/**
 * Gradient-like effect using overlay
 * Cytoscape doesn't support CSS gradients, but overlay can simulate glow
 */
export const glowingBorderStyle = {
  selector: 'node.glowing',
  style: {
    'border-width': 3,
    'border-color': '#e74c3c',
    'overlay-color': '#e74c3c',
    'overlay-opacity': 0.5,
    'overlay-padding': 6,
    'transition-property': 'overlay-opacity, overlay-padding',
    'transition-duration': '0.8s',
    'transition-timing-function': 'ease-in-out'
  }
};

/**
 * Rotating dashed border effect
 * Cytoscape supports dashed borders with patterns
 */
export const dashedRotatingBorderStyle = {
  selector: 'node.dashed',
  style: {
    'border-width': 3,
    'border-style': 'dashed',
    'border-color': '#9b59b6',
    'border-dash-pattern': [6, 3], // 6px dash, 3px gap
    'border-dash-offset': 0
  }
};

/**
 * Animate dashed border rotation
 */
export function startDashedRotation(cy, nodeSelector = 'node.dashed') {
  const nodes = cy.$(nodeSelector);
  let offset = 0;

  const interval = setInterval(() => {
    offset = (offset + 1) % 9; // Reset after full pattern cycle
    nodes.style({
      'border-dash-offset': offset
    });
  }, 50); // Smooth 60fps-ish animation

  return () => clearInterval(interval);
}

/**
 * Multi-color animated border (cycling through colors)
 */
export function startColorCycleAnimation(cy, nodeSelector, colors, intervalMs = 2000) {
  const nodes = cy.$(nodeSelector);
  let colorIndex = 0;

  const interval = setInterval(() => {
    colorIndex = (colorIndex + 1) % colors.length;
    nodes.style({
      'border-color': colors[colorIndex]
    });
  }, intervalMs);

  return () => clearInterval(interval);
}

// Example usage:
// const cleanup = startColorCycleAnimation(
//   cy,
//   'node.highlight',
//   ['#e74c3c', '#3498db', '#2ecc71', '#f39c12'],
//   1500
// );


// ============================================================================
// COMPLETE STYLE VARIANT WITH BOTH FEATURES
// ============================================================================

export const advancedStyleVariant = (colors, fontFamily) => [
  {
    selector: 'node[type = "claim"]',
    style: {
      'background-color': colors.nodeDefault,
      'label': 'data(content)',
      'color': colors.nodeText,
      'text-valign': 'center',
      'text-halign': 'center',
      'font-family': fontFamily,
      'font-size': '12px',
      'font-weight': 'normal',
      'text-wrap': 'wrap',
      'text-max-width': '200px',
      'width': 'label',
      'height': 'label',
      'min-width': '80px',
      'min-height': '40px',
      'padding': '10px',
      'shape': 'rectangle',
      'border-width': 1,
      'border-color': colors.accentBlue,
      // Smooth transitions for dynamic effects
      'transition-property': 'border-width, border-color, border-opacity',
      'transition-duration': '0.3s'
    }
  },
  {
    selector: 'node[type = "source"]',
    style: {
      'background-color': colors.nodeDefault,
      'label': 'data(title)',
      'color': colors.nodeText,
      'text-valign': 'center',
      'text-halign': 'center',
      'font-family': fontFamily,
      'font-size': '12px',
      'font-weight': 'normal',
      'text-wrap': 'wrap',
      'text-max-width': '200px',
      'width': 'label',
      'height': 'label',
      'min-width': '80px',
      'min-height': '40px',
      'padding': '10px',
      'shape': 'rectangle',
      'border-width': 1,
      'border-color': colors.accentBlueDark,
      'transition-property': 'border-width, border-color',
      'transition-duration': '0.3s'
    }
  },
  {
    selector: 'edge',
    style: {
      // Dynamic width based on rating field (0-100 scale)
      'width': 'mapData(rating, 0, 100, 1, 8)',
      'line-color': colors.accentGreen,
      'target-arrow-color': colors.accentGreen,
      'target-arrow-shape': 'triangle',
      'arrow-scale': 1,
      'curve-style': 'straight',
      // Smooth width transitions when data changes
      'transition-property': 'width',
      'transition-duration': '0.5s'
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
  // Pulsing animation for selected nodes
  {
    selector: 'node.pulsing',
    style: {
      'border-width': 4,
      'border-color': colors.accentGreen,
      'overlay-color': colors.accentGreen,
      'overlay-opacity': 0.3,
      'overlay-padding': 8
    }
  },
  // Glowing effect for highly rated nodes
  {
    selector: 'node.highly-rated',
    style: {
      'border-width': 3,
      'border-color': '#f39c12',
      'overlay-color': '#f39c12',
      'overlay-opacity': 0.4,
      'overlay-padding': 6
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
  }
];


// ============================================================================
// INTEGRATION NOTES
// ============================================================================

/**
 * TO USE RATING-BASED EDGE WIDTH:
 *
 * 1. In Graph.jsx after data loads, call enrichEdgesWithRatings():
 *
 *    useEffect(() => {
 *      if (cyRef.current && data?.elements) {
 *        enrichEdgesWithRatings(cyRef.current, apiClient)
 *          .catch(err => console.error('Failed to load ratings:', err));
 *      }
 *    }, [data]);
 *
 * 2. Update graphStyles1.js to use mapData():
 *    'width': 'mapData(rating, 0, 100, 1, 8)'
 *
 * 3. Default rating to a neutral value in formatForCytoscape():
 *    data: {
 *      ...connection.properties,
 *      rating: 50  // Default until enriched
 *    }
 */

/**
 * TO USE ANIMATED BORDERS:
 *
 * 1. Add animation styles to graphStyles1.js (see examples above)
 *
 * 2. Start animations in Graph.jsx after mount:
 *    const cleanup = startPulsingAnimation(cyRef.current, 'node.highlight');
 *    return () => cleanup(); // Stop on unmount
 *
 * 3. Control which nodes animate by adding/removing classes:
 *    node.addClass('pulsing');
 *    node.removeClass('pulsing');
 *
 * 4. For performance, limit animations to <20 nodes simultaneously
 */

/**
 * ALTERNATIVE: Use CSS animations via Cytoscape's canvas rendering
 *
 * Cytoscape can render custom overlays using HTML/CSS positioned absolutely.
 * For truly complex animations (e.g., SVG morphing, particle effects):
 * - Position absolute div over node using node.renderedPosition()
 * - Apply CSS keyframe animations to that div
 * - See PositionedOverlay.jsx pattern for reference
 */
