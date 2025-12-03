import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { fetchGraphData, fetchEntityAttribution } from '../APInterface/api.js';
import { ConnectionDisplay } from '../components/common/ConnectionDisplay.jsx';
import { AttributionProvider } from '../utilities/AttributionContext.jsx';
import { useAuth } from '../utilities/AuthContext.jsx';

/**
 * ConnectionView page - displays detailed view of a single connection
 * Receives connection ID via query parameter: /connectionview?id={connectionId}
 */
export function ConnectionView() {
  const [searchParams] = useSearchParams();
  const connectionId = searchParams.get('id');
  const { token } = useAuth();
  const [fromNodes, setFromNodes] = useState([]);
  const [toNode, setToNode] = useState(null);
  const [connectionData, setConnectionData] = useState(null);
  const [attributions, setAttributions] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadConnection = async () => {
      if (!connectionId) {
        setLoading(false);
        return;
      }

      setLoading(true);
      const response = await fetchGraphData();

      console.log('Graph data response:', response);

      if (response.error) {
        console.error('Graph data error:', response.error);
        setError(response.error);
        setLoading(false);
        return;
      }

      // Search for connection in edges
      const edge = response.data?.edges?.find(
        e => e?.connection?.properties?.id === connectionId
      );

      if (edge) {
        const composite_id = edge?.connection?.properties?.composite_id;

        // If compound, aggregate all related edges
        let relatedEdges = [edge];
        if (composite_id) {
          relatedEdges = response.data?.edges?.filter(
            e => e?.connection?.properties?.composite_id === composite_id
          );
        }

        // Build fromNodes array (deduplicate by id)
        const fromNodesMap = new Map();
        relatedEdges.forEach(e => {
          const src = e.other;
          if (!fromNodesMap.has(src.properties.id)) {
            const srcType = src.label === 'Source' ? 'source' : 'claim';
            fromNodesMap.set(src.properties.id, {
              id: src.properties.id,
              content: src.properties.content || 'No content',
              type: srcType,
              url: src.properties.url || null
            });
          }
        });
        const fromNodesArray = Array.from(fromNodesMap.values());

        // Extract target node (same for all edges in compound)
        const targetNode = edge.node;
        const targetNodeType = targetNode.label === 'Source' ? 'source' : 'claim';
        const toNodeData = {
          id: targetNode.properties.id,
          content: targetNode.properties.content || 'No content',
          type: targetNodeType,
          url: targetNode.properties.url || null
        };

        // Store connection data
        setConnectionData({
          id: connectionId,
          logicType: edge.connection.properties.logic_type,
          notes: edge.connection.properties.notes,
          compositeId: composite_id
        });

        setFromNodes(fromNodesArray);
        setToNode(toNodeData);

        // Fetch attributions for connection
        const attrMap = {};
        const connAttrResponse = await fetchEntityAttribution(connectionId, 'connection', token);
        if (!connAttrResponse.error && connAttrResponse.data) {
          attrMap[connectionId] = connAttrResponse.data;
        }

        // Fetch attributions for all source nodes
        for (const fromNode of fromNodesArray) {
          const fromAttrResponse = await fetchEntityAttribution(fromNode.id, fromNode.type, token);
          if (!fromAttrResponse.error && fromAttrResponse.data) {
            attrMap[fromNode.id] = fromAttrResponse.data;
          }
        }

        // Fetch attribution for target node
        const targetAttrResponse = await fetchEntityAttribution(targetNode.properties.id, targetNodeType, token);
        if (!targetAttrResponse.error && targetAttrResponse.data) {
          attrMap[targetNode.properties.id] = targetAttrResponse.data;
        }

        setAttributions(attrMap);
        setLoading(false);
        return;
      }

      // Connection not found
      setError('Connection not found');
      setLoading(false);
    };

    loadConnection();
  }, [connectionId, token]);

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh'
      }}>
        Loading...
      </div>
    );
  }

  if (error || !connectionId) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh'
      }}>
        {error || 'No connection ID provided'}
      </div>
    );
  }

  return (
    <AttributionProvider attributions={attributions}>
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        padding: '40px'
      }}>
        <ConnectionDisplay
          connectionId={connectionId}
          fromNodes={fromNodes}
          toNode={toNode}
          logicType={connectionData?.logicType}
          notes={connectionData?.notes}
          compositeId={connectionData?.compositeId}
        />
      </div>
    </AttributionProvider>
  );
}
