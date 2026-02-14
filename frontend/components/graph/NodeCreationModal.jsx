import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { PositionedOverlay } from './PositionedOverlay.jsx';
import { ConnectionBox } from './ConnectionBox.jsx';
import { NodeBox } from './NodeBox.jsx';
import { ConnectorLine } from './ConnectorLine.jsx';
import { createClaim, createSource, createConnection } from '../../APInterface/api.js';
import { useAuth } from '../../utilities/AuthContext.jsx';
import { formatDuplicateError } from '../../utilities/duplicateErrorFormatter.jsx';
import '../../styles/components/node-creation-panel.css';

/**
 * Node-styled panel for creating a new node (optionally connected to an existing node)
 *
 * Architecture:
 * - NodeBox components are self-contained with their own state
 * - Modal orchestrates submission sequence and tracks validation
 * - Errors are injected into specific NodeBoxes via imperative refs
 *
 * Modes:
 * - Standalone (existingNodeId=null): Creates orphan node, no ConnectionBox
 * - Connected (existingNodeId set): Creates node + connection, shows ConnectionBox
 *
 * @param {Object} props
 * @param {boolean} props.isOpen - Whether panel is visible
 * @param {Function} props.onClose - Close handler
 * @param {Object} props.node - Cytoscape node element (null for standalone mode)
 * @param {Object} props.cy - Cytoscape instance (null for standalone mode)
 * @param {Object} props.frameRef - React ref to OnClickNode frame DOM element (null for standalone mode)
 * @param {string} props.existingNodeId - UUID of node to connect to (null for standalone)
 * @param {string} props.existingNodeType - 'claim' or 'source' (null for standalone)
 * @param {string} props.existingNodeLabel - Text content of existing node (null for standalone)
 * @param {Function} props.updateAttributions - Function to update attribution cache locally
 * @param {Function} props.onGraphChange - Fallback callback for complex graph changes
 * @param {Function} props.onSuccess - Callback after successful creation: (nodeId) => void
 */
export function NodeCreationModal({ isOpen, onClose, node, cy, frameRef, existingNodeId, existingNodeType, existingNodeLabel, updateAttributions, onGraphChange, onSuccess }) {
  const { user, token, isAuthenticated } = useAuth();

  // Compound mode state
  const [isCompound, setIsCompound] = useState(false);
  const [nodeCount, setNodeCount] = useState(2); // Min 2 for compound
  const [logicType, setLogicType] = useState(null); // 'AND' or 'NAND' for compound

  // Simple mode state (only relationship - NodeBox manages node data)
  const [relationship, setRelationship] = useState(null); // 'supports', 'contradicts'
  const [currentNodeType, setCurrentNodeType] = useState(null); // Track node type for quote field visibility

  // Connection state
  const [connectionNotes, setConnectionNotes] = useState('');
  const [connectionQuote, setConnectionQuote] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // NodeBox refs for imperative control
  const nodeBoxRefs = useRef([]);

  // Validation tracking: {0: true, 1: false, ...}
  const [nodeValidations, setNodeValidations] = useState({});

  // Refs to measure actual box heights for dynamic positioning
  const [boxHeights, setBoxHeights] = useState([]);
  const [needsRecalc, setNeedsRecalc] = useState(0);

  // Callback for NodeBoxes to report validation state changes
  const handleValidationChange = useCallback((index, isValid) => {
    setNodeValidations(prev => ({ ...prev, [index]: isValid }));
  }, []);

  // Trigger recalculation when node count changes
  useEffect(() => {
    setNeedsRecalc(prev => prev + 1);
  }, [nodeCount]);

  // Measure box heights after render (for compound mode positioning)
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

  // Determine if this is standalone mode (no connection)
  const isStandalone = !existingNodeId;

  // Global validation: all boxes must be valid + connection requirements met (unless standalone)
  const canSubmit = useMemo(() => {
    if (isSubmitting) return false;

    // Standalone mode: only need node validation
    if (isStandalone) {
      return nodeValidations[0] === true;
    }

    // Connected mode: need connection notes
    if (!connectionNotes.trim()) return false;

    if (isCompound) {
      // Compound: need logic type + all nodes valid
      const expectedNodeCount = nodeCount;
      const validatedCount = Object.keys(nodeValidations).length;
      const allValid = Object.values(nodeValidations).every(v => v === true);

      return logicType && validatedCount === expectedNodeCount && allValid;
    } else {
      // Simple: need relationship + node valid
      return relationship && nodeValidations[0] === true;
    }
  }, [isCompound, nodeValidations, nodeCount, connectionNotes, logicType, relationship, isSubmitting, isStandalone]);

  if (!isOpen) return null;

  // Standalone mode doesn't require node, cy, or frameRef
  if (!isStandalone && (!node || !cy || !frameRef)) return null;

  // Triangle layout: standard gap between boxes
  const STANDARD_GAP = 24;

  // Determine connection direction based on relationship
  const getConnectionData = (newNodeId) => {
    // Simple: new node always points to existing node
    const connectionData = {
      from_node_id: newNodeId,
      to_node_id: existingNodeId,
      notes: connectionNotes.trim()
    };

    // Map relationship to logic_type (null = supports, NOT = contradicts)
    if (relationship === 'contradicts') {
      connectionData.logic_type = 'NOT';
    }

    // Add quote if provided (only valid when new node is a Source)
    if (connectionQuote.trim()) {
      connectionData.quote = connectionQuote.trim();
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
    if (!isAuthenticated || !token) {
      nodeBoxRefs.current[0]?.setError('You must be logged in to create nodes');
      return;
    }

    setIsSubmitting(true);

    try {
      // Get data from NodeBox
      const nodeData = nodeBoxRefs.current[0]?.getData();
      if (!nodeData) {
        throw new Error('Could not get node data');
      }

      const { inputMode, nodeType, content, title, url, selectedNodeId, ...metadata } = nodeData;

      let newNodeId;

      // Step 1: Create node OR use existing node
      if (inputMode === 'selected') {
        // Using existing node - skip creation
        newNodeId = selectedNodeId;
      } else {
        // Creating new node
        let nodeResult;
        if (nodeType === 'claim') {
          nodeResult = await createClaim(token, { content });
        } else {
          // Build source payload with all metadata
          const sourcePayload = {
            title,
            content,
            url: url || null,
            ...metadata // Includes source_type, authors, doi, publication_date, etc.
          };
          nodeResult = await createSource(token, sourcePayload);
        }

        if (nodeResult.error) {
          // Handle validation errors (object format from Django)
          if (typeof nodeResult.error === 'object') {
            const firstError = Object.values(nodeResult.error)[0];
            const errorMsg = Array.isArray(firstError) ? firstError[0] : firstError;
            nodeBoxRefs.current[0]?.setError(errorMsg || 'Validation error');
            setIsSubmitting(false);
            return;
          }

          // Handle title_required error (string)
          if (nodeResult.error === 'title_required') {
            nodeBoxRefs.current[0]?.setError('Source title is required');
            setIsSubmitting(false);
            return;
          }

          // Handle duplicate errors using formatter (string)
          if (typeof nodeResult.error === 'string' && nodeResult.error.startsWith('duplicate_')) {
            const formattedError = formatDuplicateError(
              nodeResult.error,
              nodeResult.data,
              nodeType
            );
            if (formattedError) {
              nodeBoxRefs.current[0]?.setError(formattedError);
              setIsSubmitting(false);
              return;
            }
          }

          // Generic error
          const errMsg = typeof nodeResult.error === 'object'
            ? JSON.stringify(nodeResult.error)
            : nodeResult.error;
          throw new Error(errMsg);
        }

        // Get the new node ID
        newNodeId = nodeResult.data.uuid || nodeResult.data.id || nodeResult.data.node_id;
        if (!newNodeId) {
          console.error('Node creation response:', nodeResult.data);
          throw new Error('Could not get ID from created node');
        }
      }

      // Step 2: Create connection (skip in standalone mode)
      if (!isStandalone) {
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
          // Only add node to cytoscape if we created a new one (not using existing)
          if (inputMode !== 'selected') {
            const nodeDisplayData = {
              id: newNodeId,
              label: nodeType === 'source' ? 'Source' : 'Claim',
              content,
              type: nodeType
            };

            if (nodeType === 'source') {
              nodeDisplayData.title = title;
              if (url) {
                nodeDisplayData.url = url;
              }
            }

            cy.add({ data: nodeDisplayData });

            // Add attribution to cache (only for newly created nodes)
            if (updateAttributions && user) {
              updateAttributions({
                add: {
                  [newNodeId]: {
                    creator: {
                      entity_uuid: newNodeId,
                      entity_type: nodeType,
                      username: user.username,
                      timestamp: new Date().toISOString(),
                      is_anonymous: false,
                      is_own: true
                    },
                    editors: []
                  }
                }
              });
            }
          }

          // Add new edge to cytoscape (always, even for existing nodes)
          const { from_node_id, to_node_id, logic_type, notes } = connectionData;
          const edgeId = connResult.data?.id || connResult.data?.uuid || `${from_node_id}-${to_node_id}`;
          cy.add({
            data: {
              id: edgeId,
              source: from_node_id,
              target: to_node_id,
              ...(logic_type ? { logic_type } : {}),
              ...(notes ? { notes } : {})
            }
          });

          // Add connection attribution to cache
          if (updateAttributions && user) {
            updateAttributions({
              add: {
                [edgeId]: {
                  creator: {
                    entity_uuid: edgeId,
                    entity_type: 'connection',
                    username: user.username,
                    timestamp: new Date().toISOString(),
                    is_anonymous: false,
                    is_own: true
                  },
                  editors: []
                }
              }
            });
          }

          // Run layout to position graph
          const layout = cy.layout({
            name: 'dagre',
            rankDir: 'BT',
            nodeSep: 80,
            rankSep: 120,
            animate: false
          });

          layout.on('layoutstop', () => {
            // Trigger compound edge bundling recalculation
            cy.trigger('recalculateBundling');
          });

          layout.run();

          handleClose();
        } catch (localUpdateError) {
          // If local update fails, fall back to full refetch
          console.error('Local graph update failed, falling back to refetch:', localUpdateError);
          if (onGraphChange) {
            onGraphChange();
          }
          handleClose();
        }
      } else {
        // Standalone mode - no graph update, just call success callback
        handleClose();
        if (onSuccess) {
          onSuccess(newNodeId);
        }
      }

    } catch (err) {
      nodeBoxRefs.current[0]?.setError(err.message || 'Failed to create node');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCreateCompound = async () => {
    if (!isAuthenticated || !token) {
      nodeBoxRefs.current[0]?.setError('You must be logged in to create nodes');
      return;
    }

    setIsSubmitting(true);

    try {
      // Step 1: Create all nodes (or use existing)
      const nodeIds = []; // Can be mix of newly created and existing IDs
      const newlyCreatedIndices = []; // Track which ones were newly created for graph update

      for (let i = 0; i < nodeBoxRefs.current.length; i++) {
        const nodeBox = nodeBoxRefs.current[i];
        if (!nodeBox) continue;

        const nodeData = nodeBox.getData();
        const { inputMode, nodeType, content, title, url, selectedNodeId, ...metadata } = nodeData;

        let nodeId;

        if (inputMode === 'selected') {
          // Using existing node - skip creation
          nodeId = selectedNodeId;
        } else {
          // Creating new node
          let result;
          if (nodeType === 'claim') {
            result = await createClaim(token, { content });
          } else {
            // Build source payload with all metadata
            const sourcePayload = {
              title,
              content,
              url: url || null,
              ...metadata // Includes source_type, authors, doi, publication_date, etc.
            };
            result = await createSource(token, sourcePayload);
          }

          if (result.error) {
            // Handle validation errors (object format from Django)
            if (typeof result.error === 'object') {
              const firstError = Object.values(result.error)[0];
              const errorMsg = Array.isArray(firstError) ? firstError[0] : firstError;
              nodeBox.setError(errorMsg || 'Validation error');
              setIsSubmitting(false);
              return;
            }

            // Handle duplicate errors - inject into SPECIFIC box that failed (string)
            if (typeof result.error === 'string' && result.error.startsWith('duplicate_')) {
              const formattedError = formatDuplicateError(
                result.error,
                result.data,
                nodeType
              );
              if (formattedError) {
                nodeBox.setError(formattedError);
              }
              setIsSubmitting(false);
              return;
            }

            // Handle other errors
            if (result.error === 'title_required') {
              nodeBox.setError('Source title is required');
              setIsSubmitting(false);
              return;
            }

            throw new Error(typeof result.error === 'object' ? JSON.stringify(result.error) : result.error);
          }

          nodeId = result.data.uuid || result.data.id || result.data.node_id;
          if (!nodeId) {
            throw new Error('Could not get ID from created node');
          }
          newlyCreatedIndices.push(i); // Track that this one was newly created
        }

        nodeIds.push(nodeId);
      }

      // Step 2: Create compound connection
      const connectionData = {
        source_node_ids: nodeIds,
        target_node_id: existingNodeId,
        logic_type: logicType,
        notes: connectionNotes.trim()
      };

      // Add quote if provided (only valid when new nodes are Sources)
      if (connectionQuote.trim()) {
        connectionData.quote = connectionQuote.trim();
      }

      const connResult = await createConnection(token, connectionData);

      if (connResult.error) {
        throw new Error(typeof connResult.error === 'object' ? JSON.stringify(connResult.error) : connResult.error);
      }

      // Step 3: Update local graph
      try {
        // Add nodes and edges to cytoscape
        for (let i = 0; i < nodeIds.length; i++) {
          const nodeId = nodeIds[i];
          const nodeData = nodeBoxRefs.current[i]?.getData();

          // Only add node to graph if it was newly created (not using existing)
          if (newlyCreatedIndices.includes(i)) {
            cy.add({
              data: {
                id: nodeId,
                label: nodeData.nodeType === 'source' ? 'Source' : 'Claim',
                content: nodeData.content,
                type: nodeData.nodeType,
                ...(nodeData.nodeType === 'source' ? {
                  title: nodeData.title,
                  ...(nodeData.url ? { url: nodeData.url } : {})
                } : {})
              }
            });

            // Add attribution (only for newly created nodes)
            if (updateAttributions && user) {
              updateAttributions({
                add: {
                  [nodeId]: {
                    creator: {
                      entity_uuid: nodeId,
                      entity_type: nodeData.nodeType,
                      username: user.username,
                      timestamp: new Date().toISOString(),
                      is_anonymous: false,
                      is_own: true
                    },
                    editors: []
                  }
                }
              });
            }
          }

          // Add edges (always, for both new and existing nodes)
          const edgeId = `${nodeId}-${existingNodeId}`;
          cy.add({
            data: {
              id: edgeId,
              source: nodeId,
              target: existingNodeId,
              logic_type: logicType,
              composite_id: connResult.data?.composite_id || connResult.data?.id,
              notes: connectionNotes.trim()
            }
          });

          // Add edge attribution to cache (only once for the compound connection)
          if (i === 0 && updateAttributions && user) {
            // Use composite_id if available, otherwise use first edge id
            const attributionId = connResult.data?.composite_id || connResult.data?.id || edgeId;
            updateAttributions({
              add: {
                [attributionId]: {
                  creator: {
                    entity_uuid: attributionId,
                    entity_type: 'connection',
                    username: user.username,
                    timestamp: new Date().toISOString(),
                    is_anonymous: false,
                    is_own: true
                  },
                  editors: []
                }
              }
            });
          }
        }

        // Run layout
        const layout = cy.layout({
          name: 'dagre',
          rankDir: 'BT',
          nodeSep: 80,
          rankSep: 120,
          animate: false
        });

        layout.on('layoutstop', () => {
          // Trigger compound edge bundling recalculation
          cy.trigger('recalculateBundling');
        });

        layout.run();

        handleClose();
      } catch (localUpdateError) {
        console.error('Local graph update failed, falling back to refetch:', localUpdateError);
        if (onGraphChange) {
          onGraphChange();
        }
        handleClose();
      }

    } catch (err) {
      // Generic error - show on first box
      nodeBoxRefs.current[0]?.setError(err.message || 'Failed to create compound connection');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    // Reset compound mode state
    setIsCompound(false);
    setNodeCount(2);
    setLogicType(null);

    // Reset simple mode state
    setRelationship(null);

    // Reset connection state
    setConnectionNotes('');

    // Reset validation tracking
    setNodeValidations({});

    // Reset all NodeBoxes
    nodeBoxRefs.current.forEach(ref => ref?.reset());

    onClose();
  };

  const handleCompoundToggle = () => {
    const newIsCompound = !isCompound;
    setIsCompound(newIsCompound);

    if (newIsCompound) {
      // Switching to compound mode
      setLogicType(null);
      setNodeCount(2);
      setNodeValidations({});
    } else {
      // Switching to simple mode
      setRelationship(null);
      setNodeValidations({});
    }
  };

  const handleNodeCountChange = (newCount) => {
    setNodeCount(newCount);
    // Validation state will be rebuilt as new NodeBoxes mount
    setNodeValidations({});
  };

  // Dynamic offset calculation based on OnClickNode frame dimensions
  const getConnectionBoxOffset = (frameRect) => {
    // Position below and to the left of frame
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

  // Standalone mode: render as centered modal without positioning overlay
  if (isStandalone) {
    return (
      <div className="modal-backdrop" onClick={handleClose}>
        <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ width: '500px', alignItems: 'stretch' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h2 className="modal-title" style={{ margin: 0 }}>Create Node</h2>
            <button
              onClick={handleClose}
              style={{
                background: 'none',
                border: 'none',
                fontSize: '24px',
                cursor: 'pointer',
                color: 'var(--modal-text)',
                padding: '0',
                lineHeight: '1',
                opacity: '0.6'
              }}
            >
              &times;
            </button>
          </div>

          <NodeBox
            ref={(el) => nodeBoxRefs.current[0] = el}
            index={0}
            onValidationChange={handleValidationChange}
            onNodeTypeChange={setCurrentNodeType}
            onClose={handleClose}
            onSubmit={handleCreate}
            isSubmitting={isSubmitting}
            showControls={true}
          />
        </div>
      </div>
    );
  }

  // Connected mode: render with positioned overlays
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
          connectionQuote={connectionQuote}
          onConnectionQuoteChange={setConnectionQuote}
          nodeCount={nodeCount}
          onNodeCountChange={handleNodeCountChange}
          currentNodeType={currentNodeType}
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
            ref={(el) => nodeBoxRefs.current[0] = el}
            index={0}
            onValidationChange={handleValidationChange}
            onNodeTypeChange={setCurrentNodeType}
            onClose={handleClose}
            onSubmit={handleCreate}
            isSubmitting={isSubmitting}
            showControls={true}
          />
        </PositionedOverlay>
      ) : (
        /* Compound mode: multiple NodeBoxes stacked vertically */
        Array.from({ length: nodeCount }).map((_, index) => (
          <PositionedOverlay
            key={index}
            domElement={frameRef}
            cy={cy}
            getOffset={(frameRect) => getNodeBoxOffset(frameRect, index, nodeCount)}
          >
            <NodeBox
              ref={(el) => nodeBoxRefs.current[index] = el}
              index={index}
              onValidationChange={handleValidationChange}
              onNodeTypeChange={(nodeType) => {
                // In compound mode, track if ANY box is a source
                if (nodeType === 'source') {
                  setCurrentNodeType('source');
                }
              }}
              onClose={handleClose}
              onSubmit={handleCreate}
              isSubmitting={isSubmitting}
              showControls={index === 0}
            />
          </PositionedOverlay>
        ))
      )}
    </>
  );
}
