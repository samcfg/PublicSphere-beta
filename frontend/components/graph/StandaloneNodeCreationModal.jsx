import { useNavigate } from 'react-router-dom';
import { NodeCreationModal } from './NodeCreationModal.jsx';

/**
 * Thin wrapper around NodeCreationModal for standalone node creation
 * (no connection to existing node)
 *
 * Used on the homepage to bootstrap new argument graphs
 *
 * @param {Object} props
 * @param {boolean} props.isOpen - Whether modal is visible
 * @param {Function} props.onClose - Close handler
 */
export function StandaloneNodeCreationModal({ isOpen, onClose }) {
  const navigate = useNavigate();

  const handleSuccess = (nodeId) => {
    // Navigate to the new node's context view
    navigate(`/context?id=${nodeId}`);
  };

  return (
    <NodeCreationModal
      isOpen={isOpen}
      onClose={onClose}
      node={null}
      cy={null}
      frameRef={null}
      existingNodeId={null}
      existingNodeType={null}
      existingNodeLabel={null}
      updateAttributions={null}
      onGraphChange={null}
      onSuccess={handleSuccess}
    />
  );
}
