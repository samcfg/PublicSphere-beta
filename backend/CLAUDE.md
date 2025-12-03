# Backend Guide
## Running

Use `uv run` for all Python commands:
- e.g. `uv run python manage.py runserver` - Start Django dev server
## Architecture

The backend coordinates two PostgreSQL databases with distinct responsibilities:

### AGE Graph Database (PS_Graph_DB/)

- Apache AGE extension provides native graph storage in PostgreSQL
- Two node types: `Claim`, `Source`
- One edge type: `Connection` with properties {id, logic_type, notes, composite_id}
- All operations through `LanguageOperations` singleton (src/language.py)
- Direct Cypher queries wrapped in SQL via AGE functions
- See ../Design Docs/data_cont.md for the custom schema and change checklist

### Django Relational Database (PS_Django_DB/)

Models are standard Django ORM. See model files for full field definitions.

**bookkeeper/** - Temporal Versioning
- `ClaimVersion`: All changes to Claim nodes
  - `node_id` (UUID FK to AGE), `content`, `operation` (CREATE/UPDATE/DELETE)
  - `valid_from`, `valid_to` (temporal interval), `timestamp`
- `SourceVersion`: All changes to Source nodes
  - `node_id` (UUID FK to AGE), `url`, `title`, `author`, `content`, etc.
  - Same temporal fields as ClaimVersion
- `EdgeVersion`: All changes to Connection edges
  - `edge_id` (UUID FK to AGE), `source_node_id`, `target_node_id`
  - `logic_type`, `composite_id`, `notes` (mirrored from AGE)
  - Same temporal fields

Pattern: Every AGE operation logged here. Temporal queries reconstruct graph at any timestamp via `valid_from/valid_to` intervals.

**users/** - Authentication & Profiles
- `User`: Django's built-in user model (username, email, password hash)
- JWT tokens generated via djangorestframework-simplejwt
- Profile data TBD (currently minimal)

**social/** - User Interactions
- `Comment`: Comments on any graph entity (node or edge)
  - `entity_uuid` (generic FK to AGE), `entity_type` ('claim'|'source'|'connection')
  - `user`, `content`, `parent` (for threading), `score` (upvotes)
- `Rating`: User ratings on graph entities
  - `entity_uuid`, `entity_type`, `user`, `score` (0-100)
  - Aggregated for display (avg_score, distribution)

**graph/** - No models (just API views coordinating with AGE)

Key Pattern: `entity_uuid` + `entity_type` allows Django models to reference AGE nodes/edges without foreign key constraints (AGE and Django are separate databases).

All API responses use `standard_response()` format: `{data, meta: {timestamp, source}, error}`

### Atomic Coordination

```python
# language.py pattern
def _execute_with_logging(self, operation_fn, log_fn):
    """Both AGE operation + Django log succeed together or rollback together"""
    # 1. Execute graph operation (AGE)
    # 2. Log to temporal tables (Django)
    # 3. If either fails, rollback both
```

### Key Patterns

**Compound Connections:**
Backend stores N separate edges with shared `composite_id` (all same target, different sources). API operations accept either individual `edge_id` or `composite_id` - try single edge first (fast path), fallback to compound query. Frontend receives individual edges, groups by `composite_id` for visualization.

**Authentication:**
JWT tokens in Authorization header. Django middleware validates token, attaches `request.user`. Unauthenticated users have read-only access to public graph data. Authenticated users can create/edit their own content, and choose per-action whether to display their username (attributed) or hide it (anonymous attribution). Moderators can delete/edit any content.