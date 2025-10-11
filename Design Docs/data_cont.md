# Data Contracts Documentation

This file tracks all locations where data schemas are defined, enforced, or consumed. When changing the data structure, update ALL listed files/functions.

## Core Data Structures

### Graph Node Types (AGE Database)
**Current Node Labels:**
- `Claim` - Assertions/conclusions in argument structure
  - **Required properties:** `id` (str, UUID)
  - **Optional properties:** `content` (str, text content)

### Graph Edge Types (AGE Database)
**Current Edge Types:**
- `Connection` - Logical relationships between Claims
  - **Required properties:** `id` (str, UUID)
  - **Optional properties:**
    - `notes` (str, interpretation/context)
    - `logic_type` (str, 'AND' or 'OR' for compound edges, NULL for single edges)
    - `composite_id` (str, UUID shared across compound edge group, NULL for single edges)


## Files That Define/Enforce Schema

### Python Backend (PS_Graph_DB/src/)

**schema.py** (Graph Schema)
- `BasicSchema.__init__()`: Defines all node/edge schema structures
- `NodeSchema` class: Node property requirements (required_properties, optional_properties)
- `EdgeSchema` class: Edge property requirements (required_properties, optional_properties)

**language.py** (Graph Operations with Atomic Logging)
- `LanguageOperations._execute_with_logging()`: Core method wrapping graph operations with version logging
  - Handles transaction atomicity (both graph + temporal log succeed or both rollback)
  - DELETE: logs first (queries intact graph), then executes Cypher
  - CREATE/UPDATE: executes Cypher first, then logs
- `LanguageOperations.create_claim()`: Creates Claim nodes with UUID id, optional content
- `LanguageOperations.create_connection()`: Creates Connection edges with UUID id, optional notes, logic_type, composite_id
- `LanguageOperations.create_compound_connection()`: Convenience function for creating compound edge groups
  - Creates multiple edges with shared composite_id, logic_type, notes
  - Returns composite_id for group operations
- `LanguageOperations.get_all_claims()`: Returns all Claim nodes
- `LanguageOperations.get_claim_connections()`: Returns connections for specific claim (individual edges with compound metadata)
- `LanguageOperations.delete_node()`: Deletes node by UUID (DETACH DELETE, cascades edges)
- `LanguageOperations.delete_edge()`: Deletes edge(s) by UUID using try-single-first pattern
  - Accepts individual edge ID or composite_id
  - Queries as individual ID first (fast path), falls back to composite_id query
  - Deletes entire compound group when composite_id provided
- `LanguageOperations.edit_node()`: Updates node properties dynamically (**kwargs)
- `LanguageOperations.edit_edge()`: Updates edge(s) properties dynamically using try-single-first pattern
  - Accepts individual edge ID or composite_id
  - Updates entire compound group when composite_id provided (synchronized metadata)
- `LanguageOperations.get_nodes_at_timestamp()`: Delegates to temporal service for historical node snapshot
- `LanguageOperations.get_edges_at_timestamp()`: Delegates to temporal service for historical edge snapshot
- `LanguageOperations.get_graph_at_timestamp()`: Delegates to temporal service for complete historical graph state

**database.py**
- `AGEDatabase.execute_cypher()`: Parses AGE JSON format
- AGE type suffix handling (::vertex, ::edge)

### Python Backend (PS_Django_DB/)

**bookkeeper/models.py** (Django ORM - Temporal Versioning)
- `NodeVersion` model: Tracks all node changes
  - Fields: `node_id` (CharField, UUID), `node_label` (CharField), `content` (TextField, nullable), `operation` (CharField: CREATE/UPDATE/DELETE), `timestamp` (DateTimeField, auto), `valid_from` (DateTimeField, auto), `valid_to` (DateTimeField, nullable), `changed_by` (CharField, nullable), `change_notes` (TextField, nullable)
  - Indexes: node_id, timestamp, (valid_from, valid_to)
- `EdgeVersion` model: Tracks all edge changes
  - Fields: `edge_id` (CharField, UUID), `edge_type` (CharField), `source_node_id` (CharField, UUID), `target_node_id` (CharField, UUID), `notes` (TextField, nullable), `logic_type` (CharField, nullable, 'AND'/'OR'), `composite_id` (CharField, nullable, UUID), `operation` (CharField: CREATE/UPDATE/DELETE), `timestamp` (DateTimeField, auto), `valid_from` (DateTimeField, auto), `valid_to` (DateTimeField, nullable), `changed_by` (CharField, nullable), `change_notes` (TextField, nullable)
  - Indexes: edge_id, timestamp, (valid_from, valid_to), (source_node_id, target_node_id), composite_id

**bookkeeper/services.py** (Temporal Queries)
- `TemporalQueryService.get_nodes_at_timestamp()`: Returns all nodes valid at given timestamp
- `TemporalQueryService.get_edges_at_timestamp()`: Returns all edges valid at given timestamp (includes logic_type, composite_id properties)
- `TemporalQueryService.get_graph_at_timestamp()`: Returns complete graph state (nodes + edges) at timestamp
- `get_temporal_service()`: Singleton accessor for service instance

**PS_Graph_DB/src/logging.py** (Version Logging Coordinator)
- `TemporalLogger.log_node_version()`: Logs node CREATE/UPDATE/DELETE to Django models
  - DELETE: Cascades to connected edges (queries logic_type, composite_id for cascade logging), closes valid_to intervals
  - UPDATE: Closes previous version (valid_to = now), creates new open version
  - CREATE: Creates new open version (valid_to = NULL)
- `TemporalLogger.log_edge_version()`: Logs edge CREATE/UPDATE/DELETE to Django models
  - Extracts and logs notes, logic_type, composite_id properties
  - Same valid_from/valid_to interval logic as nodes
- `get_temporal_logger()`: Singleton accessor for logger instance

### JavaScript Frontend (age-cytoscape-api/)

**database.js**
- `formatForCytoscape()` (lines 60-108): Converts AGE data to Cytoscape format
- Line 71: Node ID uses UUID from properties (nodeData.properties.id)
- Lines 96-97: Edge source/target correctly uses UUID (source.properties.id, target.properties.id)
- Line 98: Edge type field maps to edge.label (Connection type)
- Line 99: Property spreading (`...edge.properties`) passes through logic_type and composite_id to frontend

**index.html / graph.js**
- Cytoscape styling selectors for nodes and edges
- Edge styling differentiation planned: logic_type='AND' (blue), logic_type='OR' (orange)
- Edge tooltip displays notes, logic_type, and composite_id for compound edges
- Compound edge convergence (bezier triangulation) deferred to hierarchical arguments phase

## Data Flow

### Current Graph Operations
1. **Creation**: `language.py` operations → AGE Database (graph structure with UUIDs) + Django (temporal log)
   - Single edges: `create_connection()` with optional logic_type/composite_id
   - Compound edges: `create_compound_connection()` creates multiple edges with shared metadata
2. **Storage**: PostgreSQL with AGE extension (current graph structure) + PostgreSQL Django tables (version history)
   - AGE stores individual edges with compound metadata properties
   - Django logs all edge versions including logic_type and composite_id
3. **Retrieval (Current)**: `database.js` queries AGE → formats for Cytoscape
   - Returns individual edges with compound metadata (composite_id, logic_type)
   - Frontend groups by composite_id for visualization
4. **Retrieval (Historical)**: `language.py` → Django `TemporalQueryService` → reconstructed graph at timestamp
   - Temporal queries preserve compound edge metadata in historical snapshots
5. **Display**: `index.html` renders using Cytoscape.js
   - Individual edges rendered with color differentiation (AND=blue, OR=orange)
   - Visual convergence deferred to hierarchical arguments phase

### Integration Pattern (Hybrid Architecture)
- **AGE Graph DB**: Stores current argument structure, optimized for traversal/pathfinding
  - Individual edges with compound metadata (composite_id, logic_type)
  - Schema-less properties allow flexible edge evolution
- **Django Relational DB**: Stores complete version history, optimized for temporal queries
  - Indexes on composite_id for efficient compound edge queries
- **Atomic Coordination**: `language.py._execute_with_logging()` ensures graph operation and temporal log succeed/fail together
- **Identifier Strategy**:
  - UUIDs stored as node/edge properties in AGE, indexed in Django for consistency
  - Individual edge IDs for internal operations
  - Composite IDs for compound group operations (transparent API via try-single-first pattern)
- **Compound Edge Pattern**:
  - Backend: Multiple physical edges with shared composite_id, logic_type, notes
  - API: Transparent handling - composite_id functions like edge_id in delete/edit operations
  - Frontend: Receives individual edges, groups by composite_id for visualization

## Change Checklist

When modifying data structure:

- [x] Update `PS_Graph_DB/src/schema.py` (graph schema) node/edge definitions
- [x] Update `PS_Django_DB/bookkeeper/models.py` if adding/removing node/edge properties (create Django migration)
- [x] Update `language.py` creation/query/edit functions
- [x] Update `logging.py` if property extraction logic needs to change
- [x] Update `database.py` parsing logic if property names/types change (verified: no changes needed)
- [ ] Update `database.js` formatting logic (verified: property spreading handles new fields)
- [ ] Update `graph.js` styling selectors for compound edge visualization
- [ ] Test data flow: Python → AGE + Django → JavaScript → Frontend
- [ ] Test temporal queries: create/modify/delete → query historical state
- [x] Update this documentation

**Compound Edge Implementation Status (Oct 2025):**
- ✅ Backend schema extended (logic_type, composite_id)
- ✅ Django migration applied (0002_edgeversion_composite_id_edgeversion_logic_type)
- ✅ API operations support compound edges (create_compound_connection, transparent delete/edit)
- ✅ Temporal logging captures compound metadata
- ✅ Try-single-first pattern optimizes for single edges (majority case)
- ⏳ Frontend visualization (color differentiation planned, convergence deferred)
- ⏳ End-to-end testing

## Compound Edges: Design & Implementation

### Motivation
Multi-premise arguments require multiple source claims converging to a single conclusion. Compound edges group these logical relationships while maintaining individual edge identity for graph operations.

### Data Model
**Shared Metadata Fields (synchronized across group):**
- `composite_id` (UUID): Identifies the compound group
- `logic_type` ('AND' or 'OR'): Logical operator for the group
- `notes` (str): Shared interpretation/context

**Individual Fields (per edge):**
- `id` (UUID): Individual edge identifier
- `source_node_id`, `target_node_id`: Topology

**Constraint:** All edges in a compound group share the same target node.

### API Design Pattern: Try-Single-First
Operations accept either individual `edge_id` or `composite_id`:

1. Query as individual edge ID (fast path for majority case)
2. If not found, query as composite_id (compound group operation)
3. Apply operation to all edges in group if compound

**Example:**
```python
ops.delete_edge('abc-123')  # Could be individual ID or composite_id
# Backend tries individual lookup first, falls back to composite query
```

### Frontend Data Flow
- Backend returns individual edges with compound metadata
- Frontend receives all edges separately
- Client groups by `composite_id` for visualization
- Visual convergence (bezier triangulation) deferred to hierarchical arguments phase

### Temporal Behavior
Historical snapshots preserve compound metadata. Temporal queries return individual edges with `logic_type` and `composite_id`, allowing reconstruction of compound groups at any point in time.

## Addendum: API Response Format Standardization

### Future Concern (Post-HTTP Layer Implementation)

When exposing backends via HTTP (FastAPI/Express/Django REST), standardize response envelope across all services for consistent frontend error handling ofcombine data from multiple backends and data combination.

**Standard Response Format**:
```json
{
  "data": {},
  "meta": {
    "timestamp": "ISO-8601",
    "source": "graph_db|django|temporal"
  },
  "error": null | {"code": int, "message": str}
}
```

**Implementation Timing**:
Handle during HTTP layer development, not in core `language.py` operations. Current Python function returns can remain backend-specific until API routes are built.

**Example Use Case**:
User clicks Cytoscape node → fetch node data (graph), comments and edit history (Django) → combine into single popup UI. All three calls use same error handling logic.