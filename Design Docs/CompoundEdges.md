Claim1 -[group:123, logic:AND]→ Target
Claim2 -[group:123, logic:AND]→ Target

  # Both edges get identical metadata
  edge1_props = {
      'id': str(uuid.uuid4()),           # Individual edge ID
      'composite_id': composite_id,       # Shared group ID
      'logic_type': 'AND',
      'strength': 0.85,
      'notes': 'Both claims strongly support conclusion'
  }

  edge2_props = {
      'id': str(uuid.uuid4()),           # Different individual ID  
      'composite_id': composite_id,       # Same group ID
      'logic_type': 'AND',               # Same metadata
      'strength': 0.85,
      'notes': 'Both claims strongly support conclusion'
  }

so as a measure to make versioning easier, all of the language 
  (language.py) around the compound edges must treat them atomically, and in
   conjunction with the shared metadata, they will be effectively 
  syncronized in terms of versioning, as well as readably converging for the
   user. 
Visually the convergence of the edges will be dicteted by calculating coordinates by triangulating node positions = setting bezier control points for the two edges. This will be done in the same development step as when we make the arguments hierarchical, theoretically. 

we'll have a group of
 fields in the compound edges that have shared values always. composite_id,
 logic_type, and note. The crucial part here is that the composite_id must 
be usable in the language.py api functions as though it is another edge id.
 We should be able to put conditional handling somewhere so that the 
functions work with compound edges just the same.


 Implementation Plan

  1. Dependencies & Setup

  age-cytoscape-api/:
  npm install cytoscape-dagre dagre

  index.html: Add script after cytoscape:
  <script src="https://unpkg.com/dagre@0.8.5/dist/dagre.min.j
  s"></script>
  <script src="https://unpkg.com/cytoscape-dagre@2.5.0/cytosc
  ape-dagre.js"></script>

  2. Backend: Test Data Generation

  backend/PS_Graph_DB/src/test_data.py - Add method:
  def create_argument_hierarchy(self, graph_name: str) -> 
  dict:
      """
      Conclusion (top)
        ← Premise1, Premise2 (AND, compound)
        ← Premise3 (single)
      Premise1 (middle)
        ← Evidence1, Evidence2 (OR, compound)
      """

  3. Frontend: Dagre Integration

  graph.js:
  - Register dagre extension in init()
  - Replace applyLayout() to use dagre with rankDir: 'BT'
  - Add applyCompoundEdgeBundling() method (runs after
  layout)

  data.js:
  - Add identifyCompoundEdgeGroups() - groups edges by
  composite_id
  - Returns { groupId: [edge1, edge2, ...] }

  graph.js (new method):
  calculateBundlingControlPoints(edges, targetPos) {
      // For edges with same composite_id:
      // 1. Get source node positions
      // 2. Calculate convergence point (near target)
      // 3. Return bezier control points for each edge
  }

  4. Edge Styling

  graph.js - Update edge style selector:
  {
      selector: 'edge',
      style: {
          'curve-style': 'unbundled-bezier',  // Allow custom
   control points
          'control-point-distances': ...,
          'control-point-weights': ...
      }
  }

  Set control points dynamically after layout via
  edge.style().

  5. Database Layer

  database.js - Ensure formatForCytoscape() includes:
  composite_id: edge.properties.composite_id,
  logic_type: edge.properties.logic_type

  Execution Order

  1. Install dependencies
  2. Update database.js (ensure backend data flows correctly)
  3. Integrate dagre layout in graph.js
  4. Implement compound edge detection in data.js
  5. Add bezier bundling calculator
  6. Test and iterate

