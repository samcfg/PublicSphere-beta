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

  Step 2.2: Create wrapper in database.py
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
  - Same pattern for edges

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
