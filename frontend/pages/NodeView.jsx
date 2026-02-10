import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { fetchGraphData, fetchEntityAttribution, fetchEntityComments, fetchEntityEngagement, trackPageView } from '../APInterface/api.js';
import { NodeDisplay } from '../components/common/NodeDisplay.jsx';
import { CommentsThread } from '../components/common/CommentsThread.jsx';
import { IncomingConnectionPreview } from '../components/common/IncomingConnectionPreview.jsx';
import { SuggestedEditSidebar } from '../components/common/SuggestedEditSidebar.jsx';
import { SuggestEditModal } from '../components/graph/SuggestEditModal.jsx';
import { AttributionProvider } from '../utilities/AttributionContext.jsx';
import { useAuth } from '../utilities/AuthContext.jsx';
import { FaRegEdit } from 'react-icons/fa';

/**
 * Helper function to process incoming edges into connection previews
 * Groups by composite_id for compound connections
 */
function processIncomingConnections(incomingEdges, graphData) {
  const connectionsMap = new Map();

  incomingEdges.forEach(edge => {
    const connProps = edge.connection.properties;
    const connectionId = connProps.id;
    const compositeId = connProps.composite_id || connectionId;

    // Get or create connection entry
    if (!connectionsMap.has(compositeId)) {
      connectionsMap.set(compositeId, {
        connectionId: connectionId,
        logicType: connProps.logic_type,
        notes: connProps.notes,
        compositeId: compositeId,
        fromNodes: []
      });
    }

    // Add source node (deduplicate by id)
    const connection = connectionsMap.get(compositeId);
    const sourceNode = edge.other;
    const sourceNodeType = sourceNode.label === 'Source' ? 'source' : 'claim';

    if (!connection.fromNodes.find(n => n.id === sourceNode.properties.id)) {
      connection.fromNodes.push({
        id: sourceNode.properties.id,
        content: sourceNode.properties.content || 'No content',
        type: sourceNodeType,
        url: sourceNode.properties.url || null
      });
    }
  });

  return Array.from(connectionsMap.values());
}

/**
 * NodeView page - displays detailed view of a single node
 * Receives node ID via query parameter: /nodeview?id={nodeId}
 */
export function NodeView() {
  const [searchParams] = useSearchParams();
  const nodeId = searchParams.get('id');
  const navigate = useNavigate();
  const { user, token } = useAuth();
  const [nodeData, setNodeData] = useState(null);
  const [incomingConnections, setIncomingConnections] = useState([]);
  const [attributions, setAttributions] = useState({});
  const [comments, setComments] = useState([]);
  const [commentSort, setCommentSort] = useState('timestamp');
  const [engagement, setEngagement] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingComments, setLoadingComments] = useState(true);
  const [error, setError] = useState(null);
  const [showSuggestEditModal, setShowSuggestEditModal] = useState(false);

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

        // Fetch incoming connections (edges where this node is the target)
        const incomingEdges = response.data?.edges?.filter(
          e => e?.node?.properties?.id === nodeId
        ) || [];

        // Process and limit to 2 connections
        const processedConnections = processIncomingConnections(incomingEdges, response.data);
        setIncomingConnections(processedConnections.slice(0, 2));

        setLoading(false);
        return;
      }

      // Search for node in sources
      const source = response.data?.sources?.find(
        s => s?.source?.properties?.id === nodeId
      );

      if (source) {
        const nodeType = 'source';
        const sourceProperties = source.source.properties;

        setNodeData({
          content: sourceProperties.content || 'No content',
          type: nodeType,
          url: sourceProperties.url || null,
          // Store full source data for metadata display
          sourceData: sourceProperties
        });

        // Fetch attribution
        const attrResponse = await fetchEntityAttribution(nodeId, nodeType, token);
        if (!attrResponse.error && attrResponse.data) {
          setAttributions({ [nodeId]: attrResponse.data });
        }

        // Fetch incoming connections (edges where this node is the target)
        const incomingEdges = response.data?.edges?.filter(
          e => e?.node?.properties?.id === nodeId
        ) || [];

        // Process and limit to 2 connections
        const processedConnections = processIncomingConnections(incomingEdges, response.data);
        setIncomingConnections(processedConnections.slice(0, 2));

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

  // Track page view and fetch engagement metrics
  useEffect(() => {
    const loadEngagement = async () => {
      if (!nodeId || !nodeData) return;

      // Track this page view
      await trackPageView(nodeId, nodeData.type);

      // Fetch engagement metrics (will include the view we just tracked)
      const response = await fetchEntityEngagement(nodeId, nodeData.type);
      if (!response.error && response.data) {
        setEngagement(response.data);
      }
    };

    loadEngagement();
  }, [nodeId, nodeData]);

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
        flexDirection: 'row',
        minHeight: '100vh',
        padding: '90px 0 20px 20px',
        gap: '30px'
      }}>
        {/* Sidebar - Incoming Connections */}
        {incomingConnections.length > 0 && (
          <div style={{
            width: '550px',
            flexShrink: 0,
            display: 'flex',
            flexDirection: 'column',
            gap: '20px',
            alignItems: 'flex-start'
          }}>
            <h3 style={{
              fontSize: '18px',
              fontWeight: '600',
              color: 'var(--text-primary)',
              marginBottom: '10px',
              paddingLeft: '10px'
            }}>
              Incoming Connections
            </h3>
            {incomingConnections.map((connection) => (
              <IncomingConnectionPreview
                key={connection.compositeId}
                connectionId={connection.connectionId}
                fromNodes={connection.fromNodes}
                logicType={connection.logicType}
                notes={connection.notes}
                onClick={() => navigate(`/connectionview?id=${connection.connectionId}`)}
              />
            ))}
          </div>
        )}

        {/* Main Content */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          flex: 1,
          minWidth: 0,
          paddingRight: '20px'
        }}>
          <div style={{ position: 'relative', width: '100%', maxWidth: '920px' }}>
            <NodeDisplay
              nodeId={nodeId}
              nodeType={nodeData?.type}
              content={nodeData?.content}
              url={nodeData?.url}
              sourceData={nodeData?.sourceData}
            />

            {/* Suggest Edit Button - only show if user is NOT creator OR past edit window */}
            {(() => {
              const attribution = attributions[nodeId];
              const isCreator = attribution?.creator?.is_own === true;
              const canEdit = engagement?.edit_window?.can_edit === true;

              // Show suggest button if:
              // - User is logged in
              // - User is NOT the creator, OR user is creator but past edit window
              const shouldShowSuggest = user && (!isCreator || !canEdit);

              return shouldShowSuggest && (
                <button
                  onClick={() => setShowSuggestEditModal(true)}
                  style={{
                    position: 'absolute',
                    top: '15px',
                    right: '15px',
                    width: '24px',
                    height: '24px',
                    padding: '2px',
                    fontSize: '14px',
                    cursor: 'pointer',
                    background: 'var(--bg-secondary)',
                    border: '1px solid #d97706',
                    borderRadius: '4px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#d97706'
                  }}
                  title="Suggest improvements to this node"
                >
                  <FaRegEdit />
                </button>
              );
            })()}
          </div>

          {/* Engagement Metrics - Always show with loading/error state */}
          <div style={{
            width: '100%',
            maxWidth: '920px',
            marginTop: '20px',
            padding: '15px',
            backgroundColor: '#f5f5f5',
            border: '1px solid #ddd',
            borderRadius: '8px',
            fontSize: '14px',
            color: '#333'
          }}>
            {engagement ? (
              <>
                <div style={{ fontWeight: '600', marginBottom: '8px' }}>
                  Engagement Score: {engagement.engagement_score}
                </div>
                <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
                  <span>Views: {engagement.components.page_views}</span>
                  <span>Comments: {engagement.components.comments}</span>
                  <span>Connections: {engagement.components.connections}</span>
                  <span>Ratings: {engagement.components.ratings.count} (avg: {engagement.components.ratings.avg})</span>
                </div>
                <div style={{ marginTop: '8px', fontSize: '12px' }}>
                  Edit window: {engagement.edit_window.max_hours}h max
                  ({engagement.edit_window.hours_elapsed}h elapsed)
                  {!engagement.edit_window.can_edit && ` - ${engagement.edit_window.reason}`}
                </div>
              </>
            ) : (
              <div style={{ color: '#666' }}>Loading engagement metrics...</div>
            )}
          </div>

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

        {/* Right Sidebar - Suggested Edits */}
        <SuggestedEditSidebar
          entityUuid={nodeId}
          entityType={nodeData?.type}
          currentData={nodeData?.type === 'source' ? nodeData?.sourceData : { content: nodeData?.content }}
        />
      </div>

      {/* Suggest Edit Modal */}
      <SuggestEditModal
        isOpen={showSuggestEditModal}
        onClose={() => setShowSuggestEditModal(false)}
        nodeId={nodeId}
        nodeType={nodeData?.type}
        initialData={nodeData}
        sourceData={nodeData?.sourceData}
      />
    </AttributionProvider>
  );
}
