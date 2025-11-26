import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { fetchGraphData, fetchEntityAttribution } from '../APInterface/api.js';
import { NodeDisplay } from '../components/common/NodeDisplay.jsx';
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
  const [fromNodeData, setFromNodeData] = useState(null);
  const [toNodeData, setToNodeData] = useState(null);
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
        // Extract the "other" (from) node data
        const otherNode = edge.other;
        const otherNodeType = otherNode.label === 'Source' ? 'source' : 'claim';

        setFromNodeData({
          id: otherNode.properties.id,
          content: otherNode.properties.content || 'No content',
          type: otherNodeType,
          url: otherNode.properties.url || null
        });

        // Extract the "node" (to) node data
        const targetNode = edge.node;
        const targetNodeType = targetNode.label === 'Source' ? 'source' : 'claim';

        setToNodeData({
          id: targetNode.properties.id,
          content: targetNode.properties.content || 'No content',
          type: targetNodeType,
          url: targetNode.properties.url || null
        });

        // Fetch attributions for both nodes
        const attrMap = {};

        const otherAttrResponse = await fetchEntityAttribution(otherNode.properties.id, otherNodeType, token);
        if (!otherAttrResponse.error && otherAttrResponse.data) {
          attrMap[otherNode.properties.id] = otherAttrResponse.data;
        }

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
        flexDirection: 'row',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        padding: '20px',
        gap: '280px'
      }}>
        <NodeDisplay
          nodeId={fromNodeData?.id}
          nodeType={fromNodeData?.type}
          content={fromNodeData?.content}
          url={fromNodeData?.url}
          contentStyle={{ maxWidth: '400px' }}
        />
        <NodeDisplay
          nodeId={toNodeData?.id}
          nodeType={toNodeData?.type}
          content={toNodeData?.content}
          url={toNodeData?.url}
          contentStyle={{ maxWidth: '400px' }}
        />
      </div>
    </AttributionProvider>
  );
}
