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

    static identifyCompoundEdgeGroups(edges) {
        /**
         * Groups edges by composite_id for bundling visualization
         * Returns: Map<composite_id, Array<edge>>
         * Only includes edges that have composite_id defined
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
}

window.DataFormatter = DataFormatter;