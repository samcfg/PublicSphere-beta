import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { fetchGraphData, fetchEntityAttribution, fetchEntityComments } from '../APInterface/api.js';
import { NodeDisplay } from '../components/common/NodeDisplay.jsx';
import { CommentsThread } from '../components/common/CommentsThread.jsx';
import { IncomingConnectionsSidebar } from '../components/common/IncomingConnectionsSidebar.jsx';
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
  const [incomingConnections, setIncomingConnections] = useState([]);
  const [attributions, setAttributions] = useState({});
  const [comments, setComments] = useState([]);
  const [commentSort, setCommentSort] = useState('timestamp');
  const [loading, setLoading] = useState(true);
  const [loadingComments, setLoadingComments] = useState(true);
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

      // Parse incoming connections (edges where current node is target)
      const incomingEdges = response.data?.edges?.filter(
        e => e?.node?.properties?.id === nodeId
      ) || [];

      // Group edges by composite_id (for compound connections)
      const connectionsMap = new Map();
      incomingEdges.forEach(edge => {
        const connId = edge.connection.properties.id;
        const compositeId = edge.connection.properties.composite_id;
        const key = compositeId || connId;

        if (!connectionsMap.has(key)) {
          connectionsMap.set(key, {
            connectionId: connId,
            logicType: edge.connection.properties.logic_type,
            compositeId: compositeId,
            fromNodes: []
          });
        }

        // Add source node
        const src = edge.other;
        const srcType = src.label === 'Source' ? 'source' : 'claim';
        const existingConn = connectionsMap.get(key);

        // Avoid duplicates
        if (!existingConn.fromNodes.find(n => n.id === src.properties.id)) {
          existingConn.fromNodes.push({
            id: src.properties.id,
            content: src.properties.content || 'No content',
            type: srcType,
            url: src.properties.url || null
          });
        }
      });

      setIncomingConnections(Array.from(connectionsMap.values()));

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

  // Fetch comments separately
  const loadComments = async () => {
    if (!nodeId || !nodeData) return;

    setLoadingComments(true);
    const response = await fetchEntityComments(nodeId, commentSort, token);

    if (!response.error && response.data) {
      setComments(response.data);
    }
    setLoadingComments(false);
  };

  useEffect(() => {
    loadComments();
  }, [nodeId, commentSort, token, nodeData]);

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
        minHeight: '100vh',
        padding: '90px 20px 20px 20px',
        gap: '30px'
      }}>
        {/* Sidebar */}
        <IncomingConnectionsSidebar connections={incomingConnections} />

        {/* Main content */}
        <div style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center'
        }}>
          <NodeDisplay
            nodeId={nodeId}
            nodeType={nodeData?.type}
            content={nodeData?.content}
            url={nodeData?.url}
          />

          <div style={{
            width: '100%',
            maxWidth: '920px',
            marginTop: '40px',
            borderTop: '1px solid var(--text-primary)',
            paddingTop: '20px'
          }}>
            {loadingComments ? (
              <div>Loading comments...</div>
            ) : (
              <CommentsThread
                comments={comments}
                sortBy={commentSort}
                onSortChange={setCommentSort}
                entityUuid={nodeId}
                entityType={nodeData?.type}
                onCommentAdded={loadComments}
              />
            )}
          </div>
        </div>
      </div>
    </AttributionProvider>
  );
}
