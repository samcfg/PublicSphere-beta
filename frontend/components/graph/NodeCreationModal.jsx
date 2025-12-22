import { useState, useRef, useEffect } from 'react';
import { PositionedOverlay } from './PositionedOverlay.jsx';
import { ConnectionBox } from './ConnectionBox.jsx';
import { NodeBox } from './NodeBox.jsx';
import { ConnectorLine } from './ConnectorLine.jsx';
import { createClaim, createSource, createConnection } from '../../APInterface/api.js';
import { useAuth } from '../../utilities/AuthContext.jsx';
import '../../styles/components/node-creation-panel.css';

/**
 * Node-styled panel for creating a new node connected to an existing node
 *
 * @param {Object} props
 * @param {boolean} props.isOpen - Whether panel is visible
 * @param {Function} props.onClose - Close handler
 * @param {Object} props.node - Cytoscape node element
 * @param {Object} props.cy - Cytoscape instance
 * @param {Object} props.frameRef - React ref to OnClickNode frame DOM element (for positioning)
 * @param {string} props.existingNodeId - UUID of node to connect to
 * @param {string} props.existingNodeType - 'claim' or 'source'
 * @param {string} props.existingNodeLabel - Text content of existing node
 * @param {Function} props.updateAttributions - Function to update attribution cache locally
 * @param {Function} props.onGraphChange - Fallback callback for complex graph changes
 */
export function NodeCreationModal({ isOpen, onClose, node, cy, frameRef, existingNodeId, existingNodeType, existingNodeLabel, updateAttributions, onGraphChange }) {
  const { user, token, isAuthenticated } = useAuth();

  // Compound mode state
  const [isCompound, setIsCompound] = useState(false);
  const [nodeCount, setNodeCount] = useState(2); // Min 2 for compound
  const [logicType, setLogicType] = useState(null); // 'AND' or 'NAND' for compound

  // Simple mode state
  const [nodeType, setNodeType] = useState(null); // 'claim' or 'source'
  const [relationship, setRelationship] = useState(null); // 'supports', 'contradicts'
  const [content, setContent] = useState('');
  const [title, setTitle] = useState(''); // For sources - required
  const [url, setUrl] = useState('');

  // Compound mode: array of node data
  const [nodes, setNodes] = useState([
    { type: null, content: '', title: '', url: '' },
    { type: null, content: '', title: '', url: '' }
  ]);

  const [connectionNotes, setConnectionNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // Refs to measure actual box heights for dynamic positioning
  const nodeBoxRefs = useRef([]);
  const [boxHeights, setBoxHeights] = useState([]);
  const [needsRecalc, setNeedsRecalc] = useState(0);

  // Trigger recalculation when nodes array changes or types change
  useEffect(() => {
    setNeedsRecalc(prev => prev + 1);
  }, [nodes.length, nodes.map(n => n.type).join(',')]);

  // Measure box heights after render
  useEffect(() => {
    if (!isCompound) return;

    const heights = nodeBoxRefs.current.map(ref => {
      if (!ref) return 250; // Default fallback
      const height = ref.getBoundingClientRect().height;
      return height || 250;
    });

    if (heights.length > 0 && JSON.stringify(heights) !== JSON.stringify(boxHeights)) {
      setBoxHeights(heights);
    }
  }, [isCompound, needsRecalc]);

  if (!isOpen || !node || !cy || !frameRef) return null;

  // Truncate label for display
  const truncatedLabel = existingNodeLabel
    ? (existingNodeLabel.length > 50 ? existingNodeLabel.slice(0, 50) + '...' : existingNodeLabel)
    : existingNodeId.slice(0, 8);

  // Triangle layout: standard gap between boxes
  const STANDARD_GAP = 24; // 60% reduction from 60

  // Determine connection direction based on relationship
  const getConnectionData = (newNodeId) => {
    // Simple: new node always points to existing node
    const connectionData = {
      from_node_id: newNodeId,
      to_node_id: existingNodeId,
      notes: connectionNotes.trim()
    };

    // Map relationship to logic_type
    // null/omitted = supports (default display)
    // NOT = contradicts
    if (relationship === 'contradicts') {
      connectionData.logic_type = 'NOT';
    }

    return connectionData;
  };

  const handleCreate = async () => {
    if (!canSubmit) return;

    if (isCompound) {
      return handleCreateCompound();
    } else {
      return handleCreateSimple();
    }
  };

  const handleCreateSimple = async () => {
    // Simple mode validation
    if (!nodeType || !relationship || !content.trim() || !connectionNotes.trim()) return;

    // Source-specific validation: title is required
    if (nodeType === 'source' && !title.trim()) {
      setError('Source title is required');
      return;
    }

    if (!isAuthenticated || !token) {
      setError('You must be logged in to create nodes');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      // Step 1: Create the node
      let nodeResult;
      if (nodeType === 'claim') {
        nodeResult = await createClaim(token, { content: content.trim() });
      } else {
        nodeResult = await createSource(token, {
          title: title.trim(),
          content: content.trim(),
          url: url.trim() || null
        });
      }

      if (nodeResult.error) {
        // Handle title_required error specifically
        if (nodeResult.error === 'title_required') {
          setError('Source title is required');
          setIsSubmitting(false);
          return;
        }

        // Handle duplicate errors - All phases

        // Claim duplicates (Phase 2)
        if (nodeResult.error === 'duplicate_exact' || nodeResult.error === 'duplicate_similar') {
          const label = nodeResult.error === 'duplicate_exact'
            ? 'This claim already exists'
            : 'This claim is very similar to an existing one';
          const existingContent = nodeResult.data?.existing_content || '';
          const existingId = nodeResult.data?.existing_node_id;
          const similarity = nodeResult.data?.similarity_score;

          setError(
            <div className="duplicate-error">
              <strong>{label}</strong>
              <p style={{ fontStyle: 'italic', margin: '8px 0', fontSize: '14px' }}>
                {existingContent.slice(0, 150)}{existingContent.length > 150 ? '...' : ''}
              </p>
              {similarity && (
                <small style={{ opacity: 0.7 }}>Similarity: {(similarity * 100).toFixed(0)}%</small>
              )}
              {existingId && (
                <a
                  href={`/context?id=${existingId}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: 'var(--accent-blue)', textDecoration: 'underline', display: 'block', marginTop: '8px' }}
                >
                  View existing claim →
                </a>
              )}
            </div>
          );
          setIsSubmitting(false);
          return;
        }

        // Source URL duplicate (Phase 1)
        if (nodeResult.error === 'duplicate_url') {
          const existingTitle = nodeResult.data?.existing_title || 'Unknown';
          const existingId = nodeResult.data?.existing_node_id;
          setError(
            <div className="duplicate-error">
              <strong>This URL already exists</strong>
              <p style={{ fontStyle: 'italic', margin: '8px 0' }}>{existingTitle}</p>
              {existingId && (
                <a
                  href={`/context?id=${existingId}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: 'var(--accent-blue)', textDecoration: 'underline' }}
                >
                  View existing source →
                </a>
              )}
            </div>
          );
          setIsSubmitting(false);
          return;
        }

        // Source title duplicates (Phase 2)
        if (nodeResult.error === 'duplicate_title_exact' || nodeResult.error === 'duplicate_title_similar') {
          const label = nodeResult.error === 'duplicate_title_exact'
            ? 'A source with this title already exists'
            : 'A source with a very similar title exists';
          const existingTitle = nodeResult.data?.existing_title || 'Unknown';
          const existingId = nodeResult.data?.existing_node_id;
          const similarity = nodeResult.data?.similarity_score;

          setError(
            <div className="duplicate-error">
              <strong>{label}</strong>
              <p style={{ fontStyle: 'italic', margin: '8px 0' }}>{existingTitle}</p>
              {similarity && (
                <small style={{ opacity: 0.7 }}>Similarity: {(similarity * 100).toFixed(0)}%</small>
              )}
              {existingId && (
                <a
                  href={`/context?id=${existingId}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: 'var(--accent-blue)', textDecoration: 'underline', display: 'block', marginTop: '8px' }}
                >
                  View existing source →
                </a>
              )}
            </div>
          );
          setIsSubmitting(false);
          return;
        }

        const errMsg = typeof nodeResult.error === 'object'
          ? JSON.stringify(nodeResult.error)
          : nodeResult.error;
        throw new Error(errMsg);
      }

      // Get the new node ID - try common field names
      const newNodeId = nodeResult.data.uuid || nodeResult.data.id || nodeResult.data.node_id;
      if (!newNodeId) {
        console.error('Node creation response:', nodeResult.data);
        throw new Error('Could not get ID from created node');
      }

      // Step 2: Create the connection
      const connectionData = getConnectionData(newNodeId);
      const connResult = await createConnection(token, connectionData);

      if (connResult.error) {
        const errMsg = typeof connResult.error === 'object'
          ? JSON.stringify(connResult.error)
          : connResult.error;
        throw new Error(errMsg);
      }

      // Success - add to graph locally (no refetch needed)
      try {
        // Add new node to cytoscape with all required fields
        const nodeData = {
          id: newNodeId,
          label: nodeType === 'source' ? 'Source' : 'Claim',
          content: content.trim(),
          type: nodeType
        };

        // Add source-specific fields
        if (nodeType === 'source') {
          nodeData.title = title.trim();
          if (url.trim()) {
            nodeData.url = url.trim();
          }
        }

        cy.add({ data: nodeData });

        // Add new edge to cytoscape
        const { from_node_id, to_node_id, logic_type } = connectionData;
        cy.add({
          data: {
            id: connResult.data?.id || connResult.data?.uuid || `${from_node_id}-${to_node_id}`,
            source: from_node_id,
            target: to_node_id,
            ...(logic_type ? { logic_type } : {})
          }
        });

        // Run layout to position new node
        cy.layout({
          name: 'dagre',
          rankDir: 'BT',
          nodeSep: 80,
          rankSep: 120,
          animate: false
        }).run();

        // Add attribution to cache (current user is creator)
        if (updateAttributions && user) {
          updateAttributions({
            add: {
              [newNodeId]: {
                creator: {
                  entity_uuid: newNodeId,
                  entity_type: nodeType,
                  username: user.username,
                  timestamp: new Date().toISOString(),
                  is_anonymous: false
                },
                editors: []
              }
            }
          });
        }

        handleClose();
      } catch (localUpdateError) {
        // If local update fails, fall back to full refetch
        console.error('Local graph update failed, falling back to refetch:', localUpdateError);
        if (onGraphChange) {
          onGraphChange();
        }
        handleClose();
      }

    } catch (err) {
      setError(err.message || 'Failed to create node');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCreateCompound = async () => {
    // Compound mode: create multiple claim nodes + compound connection
    if (!logicType || !connectionNotes.trim()) return;
    if (!nodes.every(n => n.type === 'claim' && n.content.trim())) return;

    if (!isAuthenticated || !token) {
      setError('You must be logged in to create nodes');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      // Step 1: Create all claim nodes
      const createdNodeIds = [];
      for (const nodeData of nodes) {
        const result = await createClaim(token, { content: nodeData.content.trim() });

        if (result.error) {
          // Handle errors similar to simple mode
          if (result.error === 'duplicate_exact' || result.error === 'duplicate_similar') {
            const label = result.error === 'duplicate_exact'
              ? 'A claim already exists'
              : 'A claim is very similar to an existing one';
            setError(`${label}: "${result.data?.existing_content?.slice(0, 100)}..."`);
            setIsSubmitting(false);
            return;
          }
          throw new Error(typeof result.error === 'object' ? JSON.stringify(result.error) : result.error);
        }

        const newNodeId = result.data.uuid || result.data.id || result.data.node_id;
        if (!newNodeId) {
          throw new Error('Could not get ID from created node');
        }
        createdNodeIds.push(newNodeId);
      }

      // Step 2: Create compound connection
      const connResult = await createConnection(token, {
        source_node_ids: createdNodeIds,
        target_node_id: existingNodeId,
        logic_type: logicType,
        notes: connectionNotes.trim()
      });

      if (connResult.error) {
        throw new Error(typeof connResult.error === 'object' ? JSON.stringify(connResult.error) : connResult.error);
      }

      // Step 3: Update local graph
      try {
        // Add all nodes to cytoscape
        for (const [index, nodeId] of createdNodeIds.entries()) {
          cy.add({
            data: {
              id: nodeId,
              label: 'Claim',
              content: nodes[index].content.trim(),
              type: 'claim'
            }
          });

          // Add edges (each node gets its own edge with shared composite_id)
          cy.add({
            data: {
              id: `${nodeId}-${existingNodeId}`,
              source: nodeId,
              target: existingNodeId,
              logic_type: logicType,
              composite_id: connResult.data?.composite_id || connResult.data?.id
            }
          });

          // Add attribution
          if (updateAttributions && user) {
            updateAttributions({
              add: {
                [nodeId]: {
                  creator: {
                    entity_uuid: nodeId,
                    entity_type: 'claim',
                    username: user.username,
                    timestamp: new Date().toISOString(),
                    is_anonymous: false
                  },
                  editors: []
                }
              }
            });
          }
        }

        // Run layout
        cy.layout({
          name: 'dagre',
          rankDir: 'BT',
          nodeSep: 80,
          rankSep: 120,
          animate: false
        }).run();

        handleClose();
      } catch (localUpdateError) {
        console.error('Local graph update failed, falling back to refetch:', localUpdateError);
        if (onGraphChange) {
          onGraphChange();
        }
        handleClose();
      }

    } catch (err) {
      setError(err.message || 'Failed to create compound connection');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    // Reset all form state
    setIsCompound(false);
    setNodeCount(2);
    setLogicType(null);
    setNodeType(null);
    setRelationship(null);
    setContent('');
    setTitle('');
    setUrl('');
    setNodes([
      { type: null, content: '', title: '', url: '' },
      { type: null, content: '', title: '', url: '' }
    ]);
    setConnectionNotes('');
    setError(null);
    onClose();
  };

  const handleCompoundToggle = () => {
    setIsCompound(!isCompound);
    if (!isCompound) {
      // Switching to compound mode
      setLogicType(null);
      setNodeCount(2);
      setNodes([
        { type: null, content: '', title: '', url: '' },
        { type: null, content: '', title: '', url: '' }
      ]);
    }
  };

  const handleNodeCountChange = (newCount) => {
    setNodeCount(newCount);
    // Adjust nodes array
    if (newCount > nodes.length) {
      // Add more nodes
      setNodes([...nodes, ...Array(newCount - nodes.length).fill({ type: null, content: '', title: '', url: '' })]);
    } else if (newCount < nodes.length) {
      // Remove nodes
      setNodes(nodes.slice(0, newCount));
    }
  };

  const handleNodeTypeChange = (type) => {
    setNodeType(type);
    setRelationship(null); // Reset relationship when type changes
  };

  // Update individual node in compound mode
  const updateNode = (index, field, value) => {
    const newNodes = [...nodes];
    newNodes[index] = { ...newNodes[index], [field]: value };
    setNodes(newNodes);
  };

  // Validation
  const canSubmit = (() => {
    if (isSubmitting) return false;
    if (!connectionNotes.trim()) return false;

    if (isCompound) {
      // Compound mode: need logic type and all nodes filled
      if (!logicType) return false;
      // All nodes must have type and content (claims only)
      return nodes.every(n => n.type === 'claim' && n.content.trim());
    } else {
      // Simple mode: need node type, relationship, and content
      if (!nodeType || !relationship || !content.trim()) return false;
      // Sources need title
      if (nodeType === 'source' && !title.trim()) return false;
      return true;
    }
  })();

  // Dynamic offset calculation based on OnClickNode frame dimensions
  const getConnectionBoxOffset = (frameRect) => {
    if (!isCompound) {
      // Simple mode: position below and to the left of frame
      return {
        x: -STANDARD_GAP,
        y: frameRect.height + STANDARD_GAP
      };
    }
    // Compound mode: position below and to the left, vertically centered
    return {
      x: -STANDARD_GAP,
      y: frameRect.height + STANDARD_GAP
    };
  };

  const getNodeBoxOffset = (frameRect, index, totalNodes) => {
    const baseX = frameRect.width + STANDARD_GAP;
    const baseY = frameRect.height + STANDARD_GAP * 1.5;

    if (!isCompound || totalNodes === 1) {
      // Simple mode: position below and to the right of frame
      return { x: baseX, y: baseY };
    }

    // Compound mode: stack multiple boxes vertically, centered around baseY
    const heights = boxHeights.length === totalNodes
      ? boxHeights
      : Array(totalNodes).fill(250);

    const STACK_GAP = 20; // Vertical gap between stacked boxes

    // Calculate total height including gaps
    const totalHeight = heights.reduce((sum, h) => sum + h, 0) + (STACK_GAP * (totalNodes - 1));

    // Calculate Y offset for this box (distribute around baseY)
    let yOffset = baseY - totalHeight / 2;
    for (let i = 0; i < index; i++) {
      yOffset += heights[i] + STACK_GAP;
    }
    // Add half of current box height to center it
    yOffset += heights[index] / 2;

    return { x: baseX, y: yOffset };
  };

  return (
    <>
      {/* Connection Box - positioned below and left of OnClickNode frame */}
      <PositionedOverlay
        domElement={frameRef}
        cy={cy}
        getOffset={getConnectionBoxOffset}
      >
        <ConnectionBox
          isCompound={isCompound}
          onCompoundToggle={handleCompoundToggle}
          relationship={relationship}
          onRelationshipChange={setRelationship}
          logicType={logicType}
          onLogicTypeChange={setLogicType}
          connectionNotes={connectionNotes}
          onConnectionNotesChange={setConnectionNotes}
          nodeCount={nodeCount}
          onNodeCountChange={handleNodeCountChange}
        />
      </PositionedOverlay>

      {/* Node Boxes - positioned below and right of OnClickNode frame */}
      {!isCompound ? (
        /* Simple mode: single NodeBox */
        <PositionedOverlay
          domElement={frameRef}
          cy={cy}
          getOffset={(frameRect) => getNodeBoxOffset(frameRect, 0, 1)}
        >
          <NodeBox
            nodeType={nodeType}
            onNodeTypeChange={handleNodeTypeChange}
            content={content}
            onContentChange={setContent}
            title={title}
            onTitleChange={setTitle}
            url={url}
            onUrlChange={setUrl}
            onClose={handleClose}
            onSubmit={handleCreate}
            canSubmit={canSubmit}
            isSubmitting={isSubmitting}
            error={error}
            showControls={true}
          />
        </PositionedOverlay>
      ) : (
        /* Compound mode: multiple NodeBoxes stacked vertically */
        nodes.map((nodeData, index) => (
          <PositionedOverlay
            key={index}
            domElement={frameRef}
            cy={cy}
            getOffset={(frameRect) => getNodeBoxOffset(frameRect, index, nodes.length)}
          >
            <NodeBox
              ref={(el) => nodeBoxRefs.current[index] = el}
              index={index}
              nodeType={nodeData.type}
              onNodeTypeChange={(type) => updateNode(index, 'type', type)}
              content={nodeData.content}
              onContentChange={(val) => updateNode(index, 'content', val)}
              title={nodeData.title}
              onTitleChange={(val) => updateNode(index, 'title', val)}
              url={nodeData.url}
              onUrlChange={(val) => updateNode(index, 'url', val)}
              onClose={handleClose}
              onSubmit={handleCreate}
              canSubmit={canSubmit}
              isSubmitting={isSubmitting}
              error={index === 0 ? error : null}
              showControls={index === 0}
            />
          </PositionedOverlay>
        ))
      )}
    </>
  );
}
