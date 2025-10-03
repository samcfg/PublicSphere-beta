class GraphAPI {
    constructor(baseURL = 'http://localhost:3001') {
        this.baseURL = baseURL;
    }

    async fetchGraphData() {
        const response = await fetch(`${this.baseURL}/graph`);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    }

    async checkHealth() {
        const response = await fetch(`${this.baseURL}/health`);
        return await response.json();
    }
}

window.GraphAPI = GraphAPI;