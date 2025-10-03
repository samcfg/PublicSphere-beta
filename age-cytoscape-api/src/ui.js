class UIController {
    constructor() {
        this.statusDiv = document.getElementById('status');
    }

    showStatus(message, type = 'info') {
        this.statusDiv.textContent = message;
        this.statusDiv.className = type;
    }

    showSuccess(message) {
        this.showStatus(message, 'success');
    }

    showError(message) {
        this.showStatus(message, 'error');
    }

    showLoading(message = 'Loading...') {
        this.showStatus(message, '');
    }

    bindControlEvents(callbacks) {
        const loadButton = document.getElementById('load-btn');
        const resetButton = document.getElementById('reset-btn');
        const fitButton = document.getElementById('fit-btn');

        if (loadButton && callbacks.onLoad) {
            loadButton.onclick = callbacks.onLoad;
        }

        if (resetButton && callbacks.onReset) {
            resetButton.onclick = callbacks.onReset;
        }

        if (fitButton && callbacks.onFit) {
            fitButton.onclick = callbacks.onFit;
        }
    }

    updateElementCount(stats) {
        this.showSuccess(`Loaded ${stats.totalElements} elements (${stats.nodes} nodes, ${stats.edges} edges)`);
    }
}

window.UIController = UIController;