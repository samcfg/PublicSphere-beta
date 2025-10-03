class CytoscapeGraph {
    constructor(containerId) {
        this.containerId = containerId;
        this.cy = null;
        this.edgeClickActive = false;
        this.init();
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
                        'width': '80px',
                        'height': '40px',
                        'shape': 'rectangle',
                        'border-width': '2px',
                        'border-color': colors.accentBlueDark
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
                }
            ],

            layout: {
                name: 'cose',
                animate: true,
                animationDuration: 1000
            }
        });

        this.setupEdgeTooltip();
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

    applyLayout(layoutName = 'cose') {
        this.cy.layout({
            name: layoutName,
            animate: true,
            animationDuration: 1000
        }).run();
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
}

window.CytoscapeGraph = CytoscapeGraph;