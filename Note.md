  Phase 0: Django Setup
  1. Create Django project structure
  2. Define NodeVersion/EdgeVersion models matching your 
  current schema.py
  3. Run initial migration (creates tables you'd manually
  write in 001_temporal_tables.sql)
  4. Keep your current graph operations unchanged (cli.py,
  test scripts all work)  
  
  Phase 1: Database Foundation

  Step 1.1: Create relational schema

  Step 1.2: Execute migration


  Phase 2: Logging Infrastructure

  Step 2.1: Create logging.py module
  - Create PS_Graph_DB/src/logging.py
  - Create TemporalLogger class:
    - __init__(self, connection): Store PostgreSQL connection
    - log_node_version(cursor, node_id, label, properties, operation):
      - If operation == 'UPDATE': close previous version (SET valid_to = NOW())
      - Insert new row into node_versions table
      - Set valid_from = NOW(), valid_to = NULL
    - log_edge_version(cursor, edge_id, edge_type, source_id, target_id, properties, operation):
      - Same pattern for edges

  Step 2.2: Create wrapper in language.py
  - Create execute_cypher_with_logging(graph_name, query, log_context)
    - log_context = dict with:
      - entity_type: 'node' or 'edge'
      - operation: 'CREATE', 'UPDATE', or 'DELETE'
      - For nodes: {node_id, node_label, properties}
      - For edges: {edge_id, edge_type, source_id, target_id, properties}
    - Flow:
        i. Begin transaction (cursor)
      ii. Execute Cypher via existing execute_cypher()
      iii. Call temporal.log_node_version() or temporal.log_edge_version()
      iv. Commit both operations atomically (rollback on any error)

  Phase 3: Temporal Query Methods

  Step 3.1: Add get_nodes_at_timestamp() to database.py
  def get_nodes_at_timestamp(timestamp):
      # Query node_versions WHERE valid_from <= timestamp AND
   (valid_to > timestamp OR valid_to IS NULL)
      # Return snapshot of all nodes at that moment

  Step 3.2: Add get_edges_at_timestamp()
  - Same pattern for ed`ges

  Step 3.3: Add get_graph_at_timestamp()
  - Combines both queries
  - Returns complete graph state at timestamp
  - Format compatible with Cytoscape

  Phase 4: Testing

  Step 4.1: Create logging test script
  - Create claims at T0
  - Edit claim at T1
  - Create connection at T2
  - Delete claim at T3
  - Query graph at each timestamp
  - Verify reconstruction accuracy

  Step 4.2: Verify data consistency
  - Compare current graph state (from AGE) with latest
  relational versions
  - They must match exactly

  Data Flow:
  1. database.js:getGraphData() queries AGE, returns all edges individually
  2. database.js:formatForCytoscape() transforms edges to Cytoscape format
  (lines 82-105)
    - Spreads all edge properties: ...edge.properties (line 99)
    - Already passes through logic_type and composite_id without
  modification
  3. graph.js:loadElements() renders elements to canvas
  4. graph.js:setupEdgeTooltip() shows notes on edge click

  Key Finding: database.js already forwards compound edge properties to
  frontend via property spreading. No changes needed there.
  ToDo: Client-side grouping after render
  - Render all edges individually first
  - Post-processing: detect compound groups by composite_id
  - Apply visual convergence (bezier curve adjustments)
  - Pros: Preserves individual edge data, allows partial compound
  operations

We are going to implement this compound edge visualization in conjunction with a much increased involvement in cytoscape rendering. what we have now is minimal, but I want the graph to reflect the logical structure of the data as an argument map. In the map, a given node that is a conclusion (edge pointing "to") should be displayed above, and premises(from) beneath. this pattern must continue in e higherarchy, as designed in @context. 