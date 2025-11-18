import { createContext, useContext, useState } from 'react';

/**
 * AttributionContext - Stores batch-fetched attributions
 * Prevents individual API calls for each UserAttribution component
 */
const AttributionContext = createContext(null);

/**
 * AttributionProvider - Wraps components that need attribution data
 * @param {Object} props
 * @param {Object} props.attributions - Map of {uuid: {creator, editors}}
 * @param {ReactNode} props.children
 */
export function AttributionProvider({ attributions = {}, children }) {
  return (
    <AttributionContext.Provider value={attributions}>
      {children}
    </AttributionContext.Provider>
  );
}

/**
 * useAttributions - Hook to access batch attribution data
 * @returns {Object} Map of {uuid: {creator, editors}}
 */
export function useAttributions() {
  const context = useContext(AttributionContext);

  if (context === null) {
    throw new Error('useAttributions must be used within AttributionProvider');
  }

  return context;
}
