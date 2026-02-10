import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { fetchGraphData, fetchEntityAttribution, fetchEntityComments, fetchEntityEngagement, trackPageView } from '../APInterface/api.js';
import { ConnectionDisplay } from '../components/common/ConnectionDisplay.jsx';
import { CommentsThread } from '../components/common/CommentsThread.jsx';
import { SuggestedEditSidebar } from '../components/common/SuggestedEditSidebar.jsx';
import { SuggestEditModal } from '../components/graph/SuggestEditModal.jsx';
import { AttributionProvider } from '../utilities/AttributionContext.jsx';
import { useAuth } from '../utilities/AuthContext.jsx';
import { FaRegEdit } from 'react-icons/fa';

/**
 * ConnectionView page - displays detailed view of a single connection
 * Receives connection ID via query parameter: /connectionview?id={connectionId}
 */
export function ConnectionView() {
  const [searchParams] = useSearchParams();
  const connectionId = searchParams.get('id');
  const { user, token } = useAuth();
  const [fromNodes, setFromNodes] = useState([]);
  const [toNode, setToNode] = useState(null);
  const [connectionData, setConnectionData] = useState(null);
  const [attributions, setAttributions] = useState({});
  const [comments, setComments] = useState([]);
  const [commentSort, setCommentSort] = useState('timestamp');
  const [engagement, setEngagement] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingComments, setLoadingComments] = useState(true);
  const [error, setError] = useState(null);
  const [showSuggestEditModal, setShowSuggestEditModal] = useState(false);

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
              url: src.properties.url || null,
              // Store full source data for metadata display
              sourceData: srcType === 'source' ? src.properties : undefined
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
          url: targetNode.properties.url || null,
          // Store full source data for metadata display
          sourceData: targetNodeType === 'source' ? targetNode.properties : undefined
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

  // Fetch comments separately
  const loadComments = async () => {
    if (!connectionId || !connectionData) return;

    setLoadingComments(true);
    const response = await fetchEntityComments(connectionId, commentSort, token);

    if (!response.error && response.data) {
      setComments(response.data);
    }
    setLoadingComments(false);
  };

  useEffect(() => {
    loadComments();
  }, [connectionId, commentSort, token, connectionData]);

  // Track page view and fetch engagement metrics
  useEffect(() => {
    const loadEngagement = async () => {
      if (!connectionId || !connectionData) return;

      // Track this page view
      await trackPageView(connectionId, 'connection');

      // Fetch engagement metrics (will include the view we just tracked)
      const response = await fetchEntityEngagement(connectionId, 'connection');
      if (!response.error && response.data) {
        setEngagement(response.data);
      }
    };

    loadEngagement();
  }, [connectionId, connectionData]);

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
        minHeight: '100vh',
        padding: '40px 0 40px 40px'
      }}>
        {/* Main Content */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          flex: 1,
          minWidth: 0,
          paddingRight: '40px'
        }}>
          <div style={{ position: 'relative', width: '100%', maxWidth: '920px' }}>
          <ConnectionDisplay
            connectionId={connectionId}
            fromNodes={fromNodes}
            toNode={toNode}
            logicType={connectionData?.logicType}
            notes={connectionData?.notes}
            compositeId={connectionData?.compositeId}
          />

          {/* Suggest Edit Button - only show if user is NOT creator OR past edit window */}
          {(() => {
            const attribution = attributions[connectionId];
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
                title="Suggest improvements to this connection's notes"
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
              entityUuid={connectionId}
              entityType="connection"
              onCommentAdded={loadComments}
            />
          )}
        </div>
        </div>

        {/* Right Sidebar - Suggested Edits */}
        <SuggestedEditSidebar
          entityUuid={connectionId}
          entityType="connection"
          currentData={{ notes: connectionData?.notes }}
        />
      </div>

      {/* Suggest Edit Modal */}
      <SuggestEditModal
        isOpen={showSuggestEditModal}
        onClose={() => setShowSuggestEditModal(false)}
        nodeId={connectionId}
        nodeType="connection"
        initialData={{ notes: connectionData?.notes }}
        sourceData={null}
      />
    </AttributionProvider>
  );
}
