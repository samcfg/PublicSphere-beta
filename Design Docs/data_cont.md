# Data Contracts Documentation

This file tracks all locations where data schemas are defined, enforced, or consumed. When changing the data structure, update ALL listed files/functions.

## Core Data Structures

### Graph Node Types
**Current Node Labels:**
- `Claim` - Assertions/conclusions in argument structure

### Graph Edge Types
**Current Edge Types:**
- `Connection` - Logical relationships between Claims


## Files That Define/Enforce Schema

### Python Backend (PS_Graph_DB/src/)

**schema.py** (Graph Schema)
- `BasicSchema.__init__()`: Defines all node/edge schema structures
- `NodeSchema` class: Node property requirements (required_properties, optional_properties)
- `EdgeSchema` class: Edge property requirements (required_properties, optional_properties)

**language.py**
- `LanguageOperations.create_claim()`: Creates Claim nodes with properties
- `LanguageOperations.create_connection()`: Creates Connection edges with properties
- `LanguageOperations.get_all_claims()`: Returns Claim nodes
- `LanguageOperations.get_claim_connections()`: Returns connections

**database.py**
- `AGEDatabase.execute_cypher()`: Parses AGE JSON format
- AGE type suffix handling (::vertex, ::edge)

### Python Backend (PS_Rel_DB/)

**schema.py** (Relational Temporal Schema)
- `TemporalNodeSchema`: Node version history dataclass (node_id, node_label, content, operation, timestamp, valid_from, valid_to, changed_by, change_notes)
- `TemporalEdgeSchema`: Edge version history dataclass (edge_id, edge_type, source_node_id, target_node_id, notes, operation, timestamp, valid_from, valid_to, changed_by, change_notes)
- `TemporalSchema.get_table_columns()`: SQL column definitions for node_versions and edge_versions tables
- `TemporalSchema.indexes`: Temporal query index definitions
- `TemporalSchema.views`: Current version views (valid_to IS NULL)

### JavaScript Frontend (age-cytoscape-api/)

**database.js**
- `formatForCytoscape()` (lines 60-108): Converts AGE data to Cytoscape format
- Line 71: Node ID uses UUID from properties (nodeData.properties.id)
- Lines 96-97: Edge source/target correctly uses UUID (source.properties.id, target.properties.id)
- Line 98: Edge type field maps to edge.label (Connection type)

**index.html**
- Lines 58-80: Cytoscape styling expects `data.label` and `data.type`
- Line 60: Node label display
- Line 76: Edge label display

## Data Flow

1. **Creation**: `language.py` → AGE Database (with UUIDs)
2. **Storage**: PostgreSQL AGE (assigns internal IDs, stores UUID as property)
3. **Retrieval**: `database.js` queries AGE → formats for Cytoscape
4. **Display**: `index.html` renders using Cytoscape.js

## Change Checklist

When modifying data structure:

- [ ] Update `PS_Graph_DB/src/schema.py` (graph schema) definitions
- [ ] Update `PS_Rel_DB/schema.py` (temporal relational schema) if adding/changing properties
- [ ] Update `language.py` creation/query functions
- [ ] Update `database.py` parsing logic if property names/types change
- [ ] Update `database.js` formatting logic
- [ ] Update `index.html` styling selectors if needed
- [ ] Test data flow: Python → AGE → JavaScript → Frontend
- [ ] Update this documentation

## Testing Data Consistency

Run these commands to verify data contracts:
```bash
cd PS_Graph_DB && python run_test.py  # Create test data
cd ../age-cytoscape-api && node server.js  # Start API
#  http://localhost:3001/graph to inspect JSON
#  http://localhost:3001/ to test visualization
```

## Addendum: API Response Format Standardization

### Future Concern (Post-HTTP Layer Implementation)

When exposing backends via HTTP (FastAPI/Express/Django REST), standardize response envelope across all services for consistent frontend error handling and data combination.

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

**Why This Matters**:
- Frontend needs to combine data from multiple backends (graph structure + comments + temporal history)
- Single error handling pattern across all API calls
- Consistent null-checking and loading states in UI

**Implementation Timing**:
Handle during HTTP layer development, not in core `language.py` operations. Current Python function returns can remain backend-specific until API routes are built.

**Example Use Case**:
User clicks Cytoscape node → fetch node data (graph), comments (Django), edit history (temporal) → combine into single popup UI. All three calls use same error handling logic.