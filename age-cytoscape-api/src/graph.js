class CytoscapeGraph {
    constructor(containerId) {
        this.containerId = containerId;
        this.cy = null;
        this.edgeClickActive = false;
        this.init();
    }

    registerExtensions() {
        // Register dagre layout extension
        if (typeof cytoscape !== 'undefined' && typeof dagre !== 'undefined') {
            cytoscape.use(cytoscapeDagre);
        }
    }
  /**
   * Edge Click Flag System
   * 
   * Problem: Cytoscape tap events don't prevent DOM click event 
  propagation.
   * When clicking an edge, both the Cytoscape handler (shows tooltip) and
   
   * document handler (hides tooltip) fire, causing immediate hiding.
   * 
   * Solution: this.edgeClickActive flag prevents document handler from 
   * hiding tooltip during edge clicks. Flag is cleared after 50ms to 
   * allow DOM event propagation to complete.
   * 
   * Future considerations:
   * - Extend pattern for node tooltips, context menus, etc.
   * - Maintain 50ms timing for DOM propagation safety
   * - Consider this.nodeClickActive, this.backgroundClickActive flags
   */


    init() {
        // Register extensions before creating cytoscape instance
        this.registerExtensions();

        // Get CSS custom properties
        const rootStyles = getComputedStyle(document.documentElement);
        const colors = {
            bgPrimary: rootStyles.getPropertyValue('--bg-primary').trim(),
            textPrimary: rootStyles.getPropertyValue('--text-primary').trim(),
            textSecondary: rootStyles.getPropertyValue('--text-secondary').trim(),
            accentGreen: rootStyles.getPropertyValue('--accent-green').trim(),
            accentBlue: rootStyles.getPropertyValue('--accent-blue').trim(),
            accentBlueDark: rootStyles.getPropertyValue('--accent-blue-dark').trim()
        };

        this.cy = cytoscape({
            container: document.getElementById(this.containerId),

            wheelSensitivity: 0.25,

            style: [
                {
                    selector: 'node',
                    style: {
                        'background-color': colors.accentBlue,
                        'label': 'data(content)',
                        'color': colors.bgPrimary,
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'font-size': '12px',
                        'font-weight': 'bold',
                        'text-wrap': 'wrap',
                        'text-max-width': '200px',
                        'width': 'label',
                        'height': 'label',
                        'min-width': '80px',
                        'min-height': '40px',
                        'padding': '8px',
                        'shape': 'rectangle',
                        'border-width': '2px',
                        'border-color': colors.accentBlueDark
                    }
                },
                {
                    selector: 'node[label = "Source"]',
                    style: {
                        'background-color': colors.accentGreen,
                        'border-color': '#2d5a3a'  // Darker green for border
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
                        'line-color': '#e74c3c',  // Red for negation
                        'target-arrow-color': '#e74c3c'
                    }
                },
                {
                    selector: 'edge.highlighted',
                    style: {
                        'width': 5,
                        'line-color': colors.textSecondary,
                        'target-arrow-color': colors.textSecondary
                    }
                }
            ],

            layout: {
                name: 'cose',
                animate: true,
                animationDuration: 1000
            }
        });

        this.setupEdgeTooltip();
        this.setupCompoundEdgeHighlighting();
        this.setupBundlingRecalculation();
    }

    setupBundlingRecalculation() {
        /**
         * Recalculate compound edge bundling when nodes are repositioned
         * Triggers on 'free' event (when user releases dragged node)
         */
        this.cy.on('free', 'node', (event) => {
            this.applyCompoundEdgeBundling();
        });
    }

    setupCompoundEdgeHighlighting() {
        /**
         * Highlight all edges in a compound group when hovering over any one edge
         * Edges are grouped by composite_id
         */
        this.cy.on('mouseover', 'edge', (event) => {
            const edge = event.target;
            const compositeId = edge.data('composite_id');

            if (compositeId) {
                // Find all edges with same composite_id
                const compoundEdges = this.cy.edges().filter(e =>
                    e.data('composite_id') === compositeId
                );
                // Highlight all edges in the group
                compoundEdges.addClass('highlighted');
            } else {
                // Single edge without composite_id, just highlight itself
                edge.addClass('highlighted');
            }
        });

        this.cy.on('mouseout', 'edge', (event) => {
            const edge = event.target;
            const compositeId = edge.data('composite_id');

            if (compositeId) {
                // Remove highlight from all edges in group
                const compoundEdges = this.cy.edges().filter(e =>
                    e.data('composite_id') === compositeId
                );
                compoundEdges.removeClass('highlighted');
            } else {
                // Single edge, remove highlight
                edge.removeClass('highlighted');
            }
        });
    }

    setupEdgeTooltip() {
        const tooltip = document.getElementById('edge-tooltip');
        const tooltipContent = tooltip.querySelector('.tooltip-content');

        // Click on edge to show tooltip
        this.cy.on('tap', 'edge', (event) => {
            this.edgeClickActive = true;

            const edge = event.target;
            const notes = edge.data('notes') || 'No notes available';

            // Update tooltip content
            tooltipContent.textContent = notes;

            // Position tooltip near the edge
            const renderedPosition = edge.renderedMidpoint();
            const container = this.cy.container();
            const containerRect = container.getBoundingClientRect();

            tooltip.style.left = (containerRect.left + renderedPosition.x + 20) + 'px';
            tooltip.style.top = (containerRect.top + renderedPosition.y - 10) + 'px';
            tooltip.style.display = 'block';

            // Clear flag after DOM event propagation completes
            setTimeout(() => {
                this.edgeClickActive = false;
            }, 50);

            event.stopPropagation();
            event.preventDefault();
        });

        // Click outside to hide tooltip
        document.addEventListener('click', (event) => {
            if (this.edgeClickActive) return;
            if (!tooltip.contains(event.target)) {
                tooltip.style.display = 'none';
            }
        });

        // Click on cytoscape background to hide tooltip
        this.cy.on('tap', (event) => {
            if (event.target === this.cy) {
                tooltip.style.display = 'none';
            }
        });
    }

    loadElements(elements) {
        this.cy.elements().remove();
        this.cy.add(elements);
        this.applyLayout();
    }

    applyLayout(layoutName = 'dagre') {
        const layoutOptions = layoutName === 'dagre' ? {
            name: 'dagre',
            rankDir: 'BT',           // Bottom-to-Top: premises below, conclusions above
            nodeSep: 80,             // Horizontal spacing between nodes at same rank
            rankSep: 120,            // Vertical spacing between ranks
            animate: true,
            animationDuration: 1000
        } : {
            name: layoutName,
            animate: true,
            animationDuration: 1000
        };

        const layout = this.cy.layout(layoutOptions);

        layout.on('layoutstop', () => {
            // After layout completes, apply compound edge bundling
            this.applyCompoundEdgeBundling();
        });

        layout.run();
    }

    resetView() {
        this.cy.zoom(1);
        this.cy.center();
    }

    fitToScreen() {
        this.cy.fit();
    }

    getElements() {
        return this.cy.elements();
    }

    calculateBundlingControlPoints(edgeGroup, targetNode) {
        /**
         * Calculate bezier control points for compound edges to converge near target
         *
         * Strategy:
         * 1. Get positions of all source nodes and target
         * 2. Calculate convergence point (shared absolute position near target)
         * 3. For each edge, convert convergence point to relative control point
         *    (weight along source-target line, distance perpendicular to it)
         */
        const targetPos = targetNode.position();
        const sourcePositions = edgeGroup.map(edge => {
            const sourceNode = this.cy.getElementById(edge.data('source'));
            return sourceNode.position();
        });

        // Calculate centroid of source nodes
        const centroid = {
            x: sourcePositions.reduce((sum, pos) => sum + pos.x, 0) / sourcePositions.length,
            y: sourcePositions.reduce((sum, pos) => sum + pos.y, 0) / sourcePositions.length
        };

        // Convergence point: 30% from target toward centroid (absolute coordinates)
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
            const weight = Math.max(0, Math.min(1, projection)); // Clamp to [0,1]

            // Point on line at weight position
            const pointOnLineX = sourcePos.x + dx * weight;
            const pointOnLineY = sourcePos.y + dy * weight;

            // Perpendicular distance from line to convergence point
            const distX = convergencePoint.x - pointOnLineX;
            const distY = convergencePoint.y - pointOnLineY;

            // Distance is signed based on which side of the line
            // Perpendicular vector to edge (rotated 90°)
            const perpX = -ny;
            const perpY = nx;

            const distance = distX * perpX + distY * perpY;

            return {
                edge: edge,
                weight: weight,
                distance: distance
            };
        });
    }

    applyCompoundEdgeBundling() {
        /**
         * Apply bundled bezier curves to edges with shared composite_id
         */
        const edges = this.cy.edges();
        const compoundGroups = DataFormatter.identifyCompoundEdgeGroups(edges);

        compoundGroups.forEach((edgeGroup, compositeId) => {
            if (edgeGroup.length < 2) {
                // Single edge, no bundling needed
                return;
            }

            // All edges in group share same target (by design of compound edges)
            const targetNode = this.cy.getElementById(edgeGroup[0].data('target'));
            const controlPoints = this.calculateBundlingControlPoints(edgeGroup, targetNode);

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
}

window.CytoscapeGraph = CytoscapeGraph;