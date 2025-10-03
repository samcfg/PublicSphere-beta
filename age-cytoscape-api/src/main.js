class GraphApp {
    constructor() {
        this.api = new GraphAPI();
        this.ui = new UIController();
        this.graph = null;
    }

    async init() {
        this.graph = new CytoscapeGraph('cy');

        this.ui.bindControlEvents({
            onLoad: () => this.loadGraph(),
            onReset: () => this.resetView(),
            onFit: () => this.fitGraph()
        });

        await this.loadGraph();
    }

    async loadGraph() {
        this.ui.showLoading('Loading graph data...');

        try {
            const data = await this.api.fetchGraphData();

            DataFormatter.validateGraphData(data);
            const processedElements = DataFormatter.processElements(data.elements);
            const stats = DataFormatter.getElementStats(processedElements);

            this.graph.loadElements(processedElements);
            this.ui.updateElementCount(stats);

        } catch (error) {
            console.error('Error loading graph:', error);
            this.ui.showError(`Error: ${error.message}`);
        }
    }

    resetView() {
        this.graph.resetView();
    }

    fitGraph() {
        this.graph.fitToScreen();
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const app = new GraphApp();
    app.init();
});

window.GraphApp = GraphApp;