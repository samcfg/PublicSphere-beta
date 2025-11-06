# Fork, Equivalence, and Merge Operations

## Core Concept
Nodes represent ideas. Users fork nodes to modify existing ideas, link equivalent nodes via EQUIVALENT_TO edges, or (with admin approval) merge nodes when semantic identity is confirmed.

## Fork Operation
**"This idea, but slightly different"**

### Graph State
```python
# Original node remains unchanged
Node A: {id: 'A_id', content: '...'}

# New forked node created
Node B: {
  id: 'B_id',
  content: 'modified content'  # User edits after fork
}

# Optional: FORKED_FROM metadata edge
A-[:FORKED_FROM {display: false}]->B
```

### Relational Logging
```sql
fork_history:
  fork_id, source_node_id, new_node_id, forked_at, forked_by_user
```

### Key Properties
- Fork creates distinct semantic entity
- Edges remain independent (fork participates in different arguments)
- Lineage tracked via optional non-displayed graph edge OR relational table
- Temporal queries: Relational returns which forks existed at timestamp T

## Equivalence Operation (User-Level)
**"These nodes represent the same idea"**

Lightweight linking for redundant nodes—both nodes persist with independent ratings/edges, preserving authorship and argument contexts.

### Graph State
```python
Node A: {id: 'A_id', content: '...'}
Node B: {id: 'B_id', content: '...'}

A-[:EQUIVALENT_TO {created_by_user, created_at, notes}]->B
```

### Creation Flow
- String matching suggests candidates during node creation (UI "shadow" preview)
- User manually creates EQUIVALENT_TO edge or proceeds independently
- No destruction, no consent required

### Relational Logging
```sql
equivalence_links:
  link_id, node_a_id, node_b_id, created_by_user, created_at, notes

-- Cluster query (transitive closure)
WITH RECURSIVE equiv_cluster AS (
  SELECT node_b_id FROM equivalence_links WHERE node_a_id = 'A_id'
  UNION SELECT node_a_id FROM equivalence_links WHERE node_b_id = 'A_id'
  UNION
  SELECT el.node_b_id FROM equivalence_links el
  JOIN equiv_cluster ec ON el.node_a_id = ec.node_id
  UNION
  SELECT el.node_a_id FROM equivalence_links el
  JOIN equiv_cluster ec ON el.node_b_id = ec.node_id
)
```

## Merge Operation (Admin-Level)
**"Destroy duplicates—these are literally identical"**

Requires admin approval. Heavy operation for confirmed semantic identity—destroys both nodes, creates replacement. Reserved for cases where equivalence is certain and consolidation benefits clarity.

### Semantic Constraint
Only valid when nodes are semantically identical. Contradictory edges (A→X supports, B→X contradicts) indicate logical error requiring resolution before merge.

### Merge Process: A + B → C

**Graph mutations:**
```python
# 1. Delete both original nodes from graph
# A and B are removed entirely from graph database

# 2. Create replacement node
Node C: {
  id: 'C_id',
  content: user_modified_description,
  is_merged_node: true,  # Flag for UI styling
  created_at: timestamp
}

# 3. Create new edges for C
# All edges that pointed from/to A now recreated pointing from/to C
# All edges that pointed from/to B now recreated pointing from/to C
```

**Relational logging:**
```sql
merge_events:
  merge_id, source_node_ids[], replacement_node_id, merged_at, merged_by_user

node_versions:
  node_id, is_active, version_number, content, aggregate_rating, valid_from, valid_until, replaced_by

edge_history:
  edge_id, source_node_id, target_node_id, created_at, deleted_at, redirected_to
```

**Relational stores inactive merged nodes:**
- Merged nodes A and B marked `is_active: false` in `node_versions`
- `replaced_by` field points to replacement node C
- Enables temporal traceback: queries at T < merge_at return A and B as active
- Graph contains only currently active nodes (pure argument map)

### Aggregate Rating Calculation
Replacement node C receives average of A and B's aggregate ratings.

### Duplicate Edge Handling
Post-merge, if both A→X and B→X existed:
- Result: Two edges C→X (preserving attribution)
- OR deduplicate to single C→X (implementation decision pending)

## Merge Lineage Tracing

### Graph Storage (Minimal)
```python
# Graph stores only UI flag
Node C: {is_merged_node: true}
# NO merged_from array - keeps graph pure argument structure
```

### Relational Storage (Complete Lineage)
```sql
-- Direct lineage lookup
SELECT source_node_ids FROM merge_events WHERE replacement_node_id = 'C_id'
-- Returns: ['A_id', 'B_id']

-- Recursive lineage (full merge tree)
WITH RECURSIVE lineage AS (
  SELECT source_node_ids FROM merge_events WHERE replacement_node_id = 'C_id'
  UNION
  SELECT me.source_node_ids FROM merge_events me
  JOIN lineage l ON me.replacement_node_id = ANY(l.source_node_ids)
)
```

## Temporal Reconstruction

### Query Flow (Timestamp T)
1. **Relational**: Identify active nodes at T
   ```sql
   SELECT node_id FROM node_versions
   WHERE valid_from <= T AND (valid_until > T OR valid_until IS NULL)
   ```

2. **Relational**: Identify active edges at T
   ```sql
   SELECT edge_id, source_node_id, target_node_id FROM edge_history
   WHERE created_at <= T AND (deleted_at > T OR deleted_at IS NULL)
   ```

3. **Graph**: Lookup node/edge UUIDs for labels/types (starting point only)

4. **Reconstruct**: Build historical snapshot entirely from relational data

### Pre-Merge State Reconstruction
At timestamp before merge (T < merge_at):
- Relational returns A and B as active nodes
- Edge history shows original A→X and B→X connections
- C does not exist (created_at > T)
- Graph snapshot rebuilt showing pre-merge state

## Architecture Alignment

### Graph Database (PostgreSQL+AGE)
- Current argument structure only
- Contains only active nodes (merged nodes deleted from graph)
- Pure reasoning map (merged nodes appear as normal nodes)
- Metadata flag: `is_merged_node` (for UI styling)
- Optional non-displayed edges: `FORKED_FROM`

### Relational Database
- Complete fork/merge history
- Stores inactive merged nodes with `is_active: false` and `replaced_by` pointers
- Temporal reconstruction source of truth
- Lineage queries
- Edge redirection logs

### Design Principle
Graph maintains "pure argument map" philosophy - only currently active argument structure. All temporal complexity, versioning, inactive nodes, and lineage tracking handled relationally.
