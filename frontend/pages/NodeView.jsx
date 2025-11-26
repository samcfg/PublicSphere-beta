import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { fetchGraphData, fetchEntityAttribution } from '../APInterface/api.js';
import { NodeDisplay } from '../components/common/NodeDisplay.jsx';
import { AttributionProvider } from '../utilities/AttributionContext.jsx';
import { useAuth } from '../utilities/AuthContext.jsx';

/**
 * NodeView page - displays detailed view of a single node
 * Receives node ID via query parameter: /nodeview?id={nodeId}
 */
export function NodeView() {
  const [searchParams] = useSearchParams();
  const nodeId = searchParams.get('id');
  const { token } = useAuth();
  const [nodeData, setNodeData] = useState(null);
  const [attributions, setAttributions] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadNode = async () => {
      if (!nodeId) {
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

      // Search for node in claims
      const claim = response.data?.claims?.find(
        c => c?.claim?.properties?.id === nodeId
      );

      if (claim) {
        const nodeType = 'claim';
        setNodeData({
          content: claim.claim.properties.content || 'No content',
          type: nodeType
        });

        // Fetch attribution
        const attrResponse = await fetchEntityAttribution(nodeId, nodeType, token);
        if (!attrResponse.error && attrResponse.data) {
          setAttributions({ [nodeId]: attrResponse.data });
        }

        setLoading(false);
        return;
      }

      // Search for node in sources
      const source = response.data?.sources?.find(
        s => s?.source?.properties?.id === nodeId
      );

      if (source) {
        const nodeType = 'source';
        setNodeData({
          content: source.source.properties.content || 'No content',
          type: nodeType,
          url: source.source.properties.url || null
        });

        // Fetch attribution
        const attrResponse = await fetchEntityAttribution(nodeId, nodeType, token);
        if (!attrResponse.error && attrResponse.data) {
          setAttributions({ [nodeId]: attrResponse.data });
        }

        setLoading(false);
        return;
      }

      // Node not found
      setError('Node not found');
      setLoading(false);
    };

    loadNode();
  }, [nodeId, token]);

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

  if (error || !nodeId) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh'
      }}>
        {error || 'No node ID provided'}
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
        padding: '20px'
      }}>
        <NodeDisplay
          nodeId={nodeId}
          nodeType={nodeData?.type}
          content={nodeData?.content}
          url={nodeData?.url}
        />
      </div>
    </AttributionProvider>
  );
}
