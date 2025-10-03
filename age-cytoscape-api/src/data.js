class DataFormatter {
    static validateGraphData(data) {
        if (!data || !Array.isArray(data.elements)) {
            throw new Error('Invalid graph data format');
        }
        return true;
    }

    static processElements(elements) {
        return elements.map(element => {
            if (element.data) {
                return {
                    ...element,
                    data: {
                        ...element.data,
                        label: element.data.label || 'Unknown'
                    }
                };
            }
            return element;
        });
    }

    static getElementStats(elements) {
        const nodes = elements.filter(el => !el.data.source && !el.data.target);
        const edges = elements.filter(el => el.data.source && el.data.target);

        return {
            totalElements: elements.length,
            nodes: nodes.length,
            edges: edges.length
        };
    }
}

window.DataFormatter = DataFormatter;