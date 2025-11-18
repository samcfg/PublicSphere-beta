import { useState, useEffect } from 'react';
import { FaHatCowboySide } from 'react-icons/fa';
import { FaUser, FaTrash } from 'react-icons/fa';
import { fetchEntityAttribution } from '../../APInterface/api.js';
import { useAttributions } from '../../utilities/AttributionContext.jsx';

/**
 * UserAttribution component
 * Displays creator attribution for graph entities (claims, sources, connections)
 * Handles null, anonymous, and deleted user states
 *
 * @param {Object} props
 * @param {string} props.entityUuid - UUID of the entity
 * @param {string} props.entityType - 'claim' | 'source' | 'connection'
 * @param {boolean} props.showTimestamp - Show creation timestamp (default: false)
 */
export function UserAttribution({ entityUuid, entityType, showTimestamp = false }) {
  const attributionsCache = useAttributions();
  const [attribution, setAttribution] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Check cache first
    if (attributionsCache[entityUuid]) {
      setAttribution(attributionsCache[entityUuid]);
      setLoading(false);
      return;
    }

    // Fallback to individual API call if not in cache
    loadAttribution();
  }, [entityUuid, entityType, attributionsCache]);

  const loadAttribution = async () => {
    setLoading(true);
    setError(null);

    const response = await fetchEntityAttribution(entityUuid, entityType);

    if (response.error) {
      setError(response.error);
      setLoading(false);
      return;
    }

    setAttribution(response.data);
    setLoading(false);
  };

  if (loading) {
    return <span className="user-attribution loading">Loading...</span>;
  }

  if (error) {
    return <span className="user-attribution error">Error loading attribution</span>;
  }

  const creator = attribution?.creator;

  // Determine display state
  const getDisplayState = () => {
    if (!creator) {
      return { type: 'anonymous', icon: FaHatCowboySide, text: 'anonymous' };
    }

    if (creator.username === '[deleted]') {
      return { type: 'deleted', icon: FaTrash, text: 'deleted user' };
    }

    if (creator.username === '[anonymous]' || creator.is_anonymous) {
      return { type: 'anonymous', icon: FaHatCowboySide, text: 'anonymous' };
    }

    return { type: 'user', icon: FaUser, text: creator.username };
  };

  const display = getDisplayState();
  const Icon = display.icon;

  const formattedTime = creator?.timestamp
    ? new Date(creator.timestamp).toLocaleDateString()
    : null;

  return (
    <span className={`user-attribution ${display.type}`}>
      <Icon className="attribution-icon" size={14} />
      <span className="attribution-text">{display.text}</span>
      {showTimestamp && formattedTime && (
        <span className="attribution-timestamp"> • {formattedTime}</span>
      )}
    </span>
  );
}
