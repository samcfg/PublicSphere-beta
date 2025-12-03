  ## Architecture

  React single-page application built with Vite, consuming Django REST API.

  **Page Structure**:
  pages/
    Graph.jsx          - Main cytoscape visualization (full argument map)
    NodeView.jsx       - Single node detail page (query param: ?id=uuid)
    ConnectionView.jsx - Single connection detail page (query param: ?id=uuid)
    Organize.jsx       - User's content management dashboard
    Login.jsx          - Authentication

  **Component Patterns**:
  components/
    common/           - Reusable UI primitives
      NodeDisplay.jsx      - Card showing node with attribution + comments
      ConnectionDisplay.jsx - SVG curve with node endpoints
      UserAttribution.jsx   - Creator info for any entity
      CommentsRating.jsx    - Tabbed comments + ratings widget

    graph/            - Cytoscape integration
      Graph.jsx            - Main cytoscape instance + event handlers
      graphStyles1.js      - Cytoscape styling (node colors, edge curves)
      OnClickNode.jsx      - Node tooltip overlay
      OnClickEdge.jsx      - Edge tooltip overlay

  **Context Providers**:
  - `AuthContext` (utilities/AuthContext.jsx) - User state + JWT token, wraps entire app
  - `AttributionProvider` (utilities/AttributionContext.jsx) - Caches creator data for entities on
  current page

  **API Integration**:
  All API calls go through `APInterface/api.js` wrappers. Standard response format:
  ```javascript
  {
    data: {...},           // Actual response payload
    meta: {
      timestamp: ISO-8601,
      source: 'graph_db'|'users'|'social'|'temporal'
    },
    error: null | string   // Check this before using data
  }
```
  Cytoscape Graph Architecture:
  - fetchGraphData() returns {claims: [...], sources: [...], edges: [...]}
  - Formatters convert to cytoscape format: {nodes: [{data: {id, label, ...}}], edges: [{data: {source,
   target, ...}}]}
  - Graph styling (graphStyles1.js):
    - Nodes: Claims (blue rectangles), Sources (green rounded rectangles)
    - Edges: Positive (green), Negative (red), compound edges bundled with bezier curves
  - Click handlers spawn overlay components (OnClickNode, OnClickEdge) positioned absolutely

  Design System:
  CSS variables in styles/variables.css:
  --accent-green: #68d391   /* Positive connections (AND/OR), source nodes */
  --accent-red: #e74c3c     /* Negative connections (NOT/NAND) */
  --accent-blue: #8a9ba8    /* Claim nodes, UI borders */
  --bg-primary: ...         /* Background colors (light/dark mode) */
  --text-primary: ...       /* Text colors (light/dark mode) */

  Routing: React Router v6, routes defined in main.jsx. Query params used for entity IDs (?id=uuid), no
   path params.
