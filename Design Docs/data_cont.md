# Data Contracts Documentation

This file tracks all locations where data schemas are defined, enforced, or consumed. When changing the data structure, update ALL listed files/functions.

## Core Data Structures

### Graph Node Types (AGE Database)
**Current Node Labels:**
- `Claim` - Assertions/conclusions in argument structure
  - **Required properties:** `id` (str, UUID)
  - **Optional properties:** `content` (str, text content)
- `Source` - Evidence, observations, citations
  - **Required properties:** `id` (str, UUID), `title` (str), `source_type` (str)
  - **Optional properties (universal):** `thumbnail_link` (str), `authors` (JSONB array), `url` (str), `accessed_date` (str, ISO 8601), `excerpt` (str), `content` (str, user summary)
  - **Optional properties (publication metadata):** `publication_date` (str, ISO 8601 or partial), `container_title` (str, journal/book/website/conference name), `publisher` (str), `publisher_location` (str), `volume` (str), `issue` (str), `pages` (str, e.g., "123-145")
  - **Optional properties (book-specific):** `edition` (str)
  - **Optional properties (identifiers):** `doi` (str, Digital Object Identifier), `isbn` (str), `issn` (str), `pmid` (str, PubMed ID), `pmcid` (str, PubMed Central ID), `arxiv_id` (str), `handle` (str), `persistent_id` (str), `persistent_id_type` (str)
  - **Optional properties (contributors):** `editors` (JSONB array, [{name, role}])
  - **Optional properties (legal sources):** `jurisdiction` (str), `legal_category` (str, 'case'|'statute'|'regulation'|'treaty'), `court` (str), `decision_date` (str), `case_name` (str), `code` (str), `section` (str)
  - **Optional properties (overflow):** `metadata` (JSONB, type-specific edge cases)
  - **source_type values:** 'journal_article', 'preprint', 'book', 'website', 'newspaper', 'magazine', 'thesis', 'conference_paper', 'technical_report', 'government_document', 'dataset', 'media', 'legal', 'testimony'
  - **Type-specific validation:** Legal sources require `jurisdiction` and `legal_category`

**IMPORTANT:** When changing Source node structure, update ALL files listed in "Change Checklist" section below. See SourceNodeCiteFormat.md for detailed type-specific field requirements and citation system design rationale.

### Graph Edge Types (AGE Database)
**Current Edge Types:**
- `Connection` - Logical relationships between any nodes (Claim ↔ Claim, Source → Claim, Claim → Source, Source ↔ Source)
  - **Required properties:** `id` (str, UUID)
  - **Optional properties:**
    - `notes` (str, interpretation/context)
    - `logic_type` (str, 'AND'|'OR'|'NOT'|'NAND' - validated at creation)
    - `composite_id` (str, UUID shared across compound edge group, NULL for single edges)
    - `quote` (str, excerpt from source node when connection originates FROM a Source, max 500 chars for fair use)

## Files That Define/Enforce Schema

### Graph Backend (PS_Graph_DB/src/)

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
- `LanguageOperations.create_source()`: Creates Source nodes with UUID id, optional url, title, author, publication_date, source_type, content
- `LanguageOperations.create_connection()`: Creates Connection edges between any nodes with UUID id, optional notes, logic_type, composite_id, quote
  - Validates logic_type against {'AND', 'OR', 'NOT', 'NAND'}
  - Accepts from_node_id/to_node_id (works with Claims, Sources, any future node types)
  - Quote field: optional excerpt from source node (max 500 chars, for fair use commentary)
- `LanguageOperations.create_compound_connection()`: Convenience function for creating compound edge groups
  - Creates multiple edges with shared composite_id, logic_type, notes, quote
  - Validates logic_type at entry
  - Returns composite_id for group operations
- `LanguageOperations.get_all_claims()`: Returns all Claim nodes
- `LanguageOperations.get_all_sources()`: Returns all Source nodes
- `LanguageOperations.get_node_connections()`: Returns all connections from/to a specific node (bidirectional, works for any node type)
- `LanguageOperations.delete_node()`: Deletes node by UUID (DETACH DELETE, cascades edges). Queries all properties for proper logging (Claim: content; Source: url, title, author, publication_date, source_type, content)
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

### Relational Backend (PS_Django_DB/)

**bookkeeper/models.py** (Django ORM - Temporal Versioning)
- `ClaimVersion` model: Tracks all Claim node changes
  - Fields: `node_id` (CharField, UUID), `content` (TextField, nullable), `operation` (CharField: CREATE/UPDATE/DELETE), `timestamp` (DateTimeField, auto), `valid_from` (DateTimeField, auto), `valid_to` (DateTimeField, nullable), `changed_by` (CharField, nullable), `change_notes` (TextField, nullable), `version_number` (IntegerField, sequential)
  - **Search fields:** `content_search` (SearchVectorField, auto-populated by DB trigger), `content_normalized` (TextField, canonical form for exact duplicates)
  - Indexes: node_id, timestamp, (valid_from, valid_to), (node_id, version_number), GIN(content_search), GIN(content trigram)
  - Table: `claim_versions`
- `SourceVersion` model: Tracks all Source node changes
  - Fields: All Source properties (title, source_type, authors, url, doi, publication_date, etc.), `operation` (CharField: CREATE/UPDATE/DELETE), `timestamp` (DateTimeField, auto), `valid_from` (DateTimeField, auto), `valid_to` (DateTimeField, nullable), `changed_by` (CharField, nullable), `change_notes` (TextField, nullable), `version_number` (IntegerField, sequential)
  - **Search fields:** `title_search` (SearchVectorField, auto-populated by DB trigger), `title_normalized` (TextField, canonical form for exact duplicates)
  - **Deduplication fields:** `url_normalized` (CharField, canonical URL form), `doi_normalized` (CharField, lowercase without prefix)
  - Indexes: node_id, timestamp, (valid_from, valid_to), (node_id, version_number), source_type, url_normalized, doi_normalized, publication_date, GIN(title_search), GIN(title trigram)
  - Table: `source_versions`
- `EdgeVersion` model: Tracks all edge changes
  - Fields: `edge_id` (CharField, UUID), `edge_type` (CharField), `source_node_id` (CharField, UUID), `target_node_id` (CharField, UUID), `notes` (TextField, nullable), `logic_type` (CharField, nullable, 'AND'|'OR'|'NOT'|'NAND'), `composite_id` (CharField, nullable, UUID), `quote` (TextField, nullable, max 500 chars for fair use), `operation` (CharField: CREATE/UPDATE/DELETE), `timestamp` (DateTimeField, auto), `valid_from` (DateTimeField, auto), `valid_to` (DateTimeField, nullable), `changed_by` (CharField, nullable), `change_notes` (TextField, nullable)
  - Indexes: edge_id, timestamp, (valid_from, valid_to), (source_node_id, target_node_id), composite_id
  - Table: `edge_versions`

**bookkeeper/services.py** (Temporal Queries)
- `TemporalQueryService.get_nodes_at_timestamp()`: Returns all nodes (Claims and Sources) valid at given timestamp
  - Queries both ClaimVersion and SourceVersion tables
  - Reconstructs node dicts with proper labels and type-specific properties
- `TemporalQueryService.get_edges_at_timestamp()`: Returns all edges valid at given timestamp (includes logic_type, composite_id properties)
- `TemporalQueryService.get_graph_at_timestamp()`: Returns complete graph state (nodes + edges) at timestamp
- `get_temporal_service()`: Singleton accessor for service instance

**PS_Graph_DB/src/logging.py** (Version Logging Coordinator)
- `TemporalLogger.log_node_version()`: Logs node CREATE/UPDATE/DELETE to Django models
  - Dispatches based on node label: Claim → ClaimVersion, Source → SourceVersion
  - DELETE: Cascades to connected edges (queries logic_type, composite_id for cascade logging), closes valid_to intervals
  - UPDATE: Closes previous version (valid_to = now), creates new open version (increments version_number)
  - CREATE: Creates new open version (valid_to = NULL, version_number = 1)
  - Raises ValueError for unknown node labels
- `TemporalLogger.log_edge_version()`: Logs edge CREATE/UPDATE/DELETE to Django models
  - Extracts and logs notes, logic_type, composite_id, quote properties
  - Same valid_from/valid_to interval logic as nodes
- `get_temporal_logger()`: Singleton accessor for logger instance

**graph/services.py** (Search & Deduplication)
- `DeduplicationService.check_duplicate_claim()`: Pre-creation duplicate detection for claims
  - Strategy: Exact match on `content_normalized` → trigram similarity > 0.85
  - Returns: `{duplicate_type: 'exact'|'similar', existing_id, existing_content, similarity_score}` or None
  - High threshold (0.85) minimizes false positives
- `DeduplicationService.check_duplicate_source()`: Four-tier source deduplication
  - Priority order: DOI normalized → URL normalized → title exact → title trigram (0.85)
  - Returns: `{duplicate_type: 'doi'|'url'|'title_exact'|'title_similar', existing_id, existing_title, existing_url, similarity_score}` or None
  - Source `content` field NOT checked (it's user's personal summary, not canonical)
- `SearchService.search_nodes()`: Full-text search across claims and sources
  - Uses PostgreSQL full-text search (SearchVector) + trigram matching
  - Lower threshold (0.3) for broad discovery vs deduplication
  - Queries `valid_to IS NULL` for current versions only

**graph/utils.py** (Normalization)
- `normalize_url(url)`: Canonical URL form for duplicate detection
  - Rules: lowercase, remove protocol/www/trailing slash/query params/fragments
  - Example: `'HTTPS://WWW.Example.com/Article?utm=fb'` → `'example.com/article'`
- `normalize_content(content)`: Canonical text form (claims and source titles)
  - Rules: lowercase, trim whitespace, collapse multiple spaces
- `normalize_doi(doi)`: Canonical DOI form
  - Rules: lowercase, strip prefixes (https://doi.org/, doi:, etc.), validate starts with '10.'
  - Example: `'DOI: 10.1234/FOO'` → `'10.1234/foo'`

### React Frontend (frontend/)

**Data Format**: Frontend receives graph data via Django REST API (`GET /api/graph/graph/`)
- Response format: `{data: {claims: [...], sources: [...], edges: [...]}, meta: {...}, error: null}`
- Claims: `{claim: {properties: {id, content}}}`
- Sources: `{source: {properties: {id, title, source_type, authors, url, ...}}}` (all citation fields)
- Edges: `{connection: {properties: {id, notes, logic_type, composite_id, quote}}, source_node: {properties: {id}}, target_node: {properties: {id}}}`

**Cytoscape Integration**: React components convert AGE format to Cytoscape.js elements
- Node styling by label: Claims (blue), Sources (green)
- Edge styling by logic_type: AND/OR (blue/orange), NOT/NAND (red)
- Compound edge visualization: Edges with shared `composite_id` grouped/bundled visually
- Property spreading ensures all fields automatically available in frontend

## Data Flow

### Current Graph Operations
1. **Creation**: `language.py` operations → AGE Database (graph structure with UUIDs) + Django (temporal log)
   - Single edges: `create_connection()` with optional logic_type/composite_id/quote
   - Compound edges: `create_compound_connection()` creates multiple edges with shared metadata (including quote)
2. **Storage**: PostgreSQL with AGE extension (current graph structure) + PostgreSQL Django tables (version history)
   - AGE stores individual edges with compound metadata properties
   - Django logs all edge versions including logic_type and composite_id
3. **Retrieval (Current)**: React → Django REST API → AGE query → format response
   - Django `/api/graph/graph/` endpoint returns full graph in AGE format
   - React converts to Cytoscape.js elements (nodes + edges)
   - Individual edges with compound metadata (composite_id, logic_type) grouped for visualization
4. **Retrieval (Historical)**: Django API → `TemporalQueryService` → reconstructed graph at timestamp
   - Temporal queries preserve compound edge metadata in historical snapshots
5. **Display**: React components render Cytoscape.js graph
   - Node styling by type (Claim/Source), edge styling by logic_type
   - Compound edge bundling via shared composite_id

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
  - Backend: Multiple physical edges with shared composite_id, logic_type, notes, quote
  - API: Transparent handling - composite_id functions like edge_id in delete/edit operations
  - Frontend: Receives individual edges, groups by composite_id for visualization

## Change Checklist

When modifying data structure:

- [ ] Update `PS_Graph_DB/src/schema.py` (graph schema) node/edge definitions
- [ ] Update `PS_Django_DB/bookkeeper/models.py` if adding/removing node/edge properties. Then change  `logging.py`, `services.py` and `admin.py` . Then, makemigrations; migrate. 
- [ ] Update `language.py` creation/query/edit functions
- [ ] Update `database.py` parsing logic if property names/types change
- [ ] Update `graph/serializers.py` for API validation
- [ ] Update React Cytoscape formatting/styling (frontend component files)
- [ ] Test data flow: Python → AGE + Django → JavaScript → Frontend
- [ ] Test temporal queries: create/modify/delete → query historical state
- [ ] Update this documentation


## HTTP API Layer (Django REST Framework)

### Overview

The Django backend serves as the primary HTTP API for all frontend operations. All endpoints use function-based views (`@api_view` decorator) with standardized response format.

### Standard Response Format

All endpoints return responses wrapped by `standard_response()` (common/api_standards.py):

```json
{
  "data": {},
  "meta": {
    "timestamp": "ISO-8601",
    "source": "graph_db|django|temporal|citation_fetcher"
  },
  "error": null | "error message" | {"field": "error details"}
}
```

**HTTP Status Codes**:
- 200 OK - Successful retrieval/update
- 201 Created - Successful creation
- 400 Bad Request - Validation errors (serializer.errors in error field)
- 401 Unauthorized - Authentication required
- 403 Forbidden - Ownership/time window violations
- 404 Not Found - Entity not found
- 409 Conflict - Duplicate detection
- 500 Internal Server Error - Unhandled exceptions

### API Endpoints

**Base URL Pattern**: `/api/graph/` (configured in PS_Django_DB/graph/urls.py)

#### Claims

**GET /claims/** - List all claims
- Auth: Optional (read-only without auth)
- Returns: `{data: {claims: [...]}, meta: {...}, error: null}`

**POST /claims/** - Create claim
- Auth: Optional (anonymous creation allowed)
- Body: `{content: str (optional)}`
- Validation: Duplicate detection (Phase 2 - exact + fuzzy matching)
- Returns 409 on duplicate: `{error: "duplicate_exact|duplicate_fuzzy", data: {existing_node_id, existing_content, similarity_score}}`
- Returns 201: `{data: {id: uuid}, ...}`

**GET /claims/{claim_id}/** - Get claim connections
- Auth: Optional
- Returns: `{data: {connections: [...]}, ...}`

**PATCH /claims/{claim_id}/** - Update claim
- Auth: Required
- Guards: Ownership check, time window check (engagement-adjusted)
- Body: Dynamic properties (any valid Claim fields)
- Returns 403: `{error: "Only the creator can edit..." | "Edit window expired..."}`
- Returns: `{data: {id: uuid, updated: true}, ...}`

**DELETE /claims/{claim_id}/** - Delete claim
- Auth: Required
- Guards: Same as PATCH
- Cascades: Deletes all connected edges, closes version intervals
- Returns: `{data: {id: uuid, deleted: true}, ...}`

#### Sources

**GET /sources/** - List all sources
- Auth: Optional
- Returns: `{data: {sources: [...]}, ...}`

**POST /sources/** - Create source
- Auth: Optional
- Body: See SourceCreateSerializer (graph/serializers.py:59-100)
  - Required: `title` (str), `source_type` (choice)
  - Optional: All citation fields (authors, doi, url, publication_date, container_title, publisher, volume, issue, pages, isbn, issn, accessed_date, metadata, content, etc.)
- Validation: Duplicate detection (DOI > URL > title fuzzy)
- Returns 400 on missing title: `{error: "title_required", message: "Source title is required"}`
- Returns 409 on duplicate: `{error: "duplicate_doi|duplicate_url|duplicate_fuzzy", data: {existing_node_id, existing_title, existing_url, similarity_score}}`
- Returns 201: `{data: {id: uuid}, ...}`

**POST /sources/fetch-metadata/** - Fetch citation metadata
- Auth: None (AllowAny)
- Body: `{url: str}` OR multipart form with `pdf_file`
- Returns: `{data: {success: bool, source: 'crossref|arxiv|html_meta|pdf|fallback', confidence: 'high|medium|low', metadata: {...}}, ...}`
- Used for: Pre-filling source creation form with scraped/API data

**GET /sources/{source_id}/** - Get source connections
- Auth: Optional
- Returns: `{data: {connections: [...]}, ...}`

**PATCH /sources/{source_id}/** - Update source
- Auth: Required
- Guards: Ownership check, time window check
- Body: Dynamic properties
- Returns: Similar to claims PATCH

**DELETE /sources/{source_id}/** - Delete source
- Auth: Required
- Guards: Same as PATCH
- Returns: Similar to claims DELETE

#### Connections

**POST /connections/** - Create connection (single or compound)
- Auth: Optional
- Body (single): `{from_node_id: uuid, to_node_id: uuid, notes?: str, logic_type?: 'AND|OR|NOT|NAND', composite_id?: uuid, quote?: str}`
- Body (compound): `{source_node_ids: [uuid, uuid, ...], target_node_id: uuid, logic_type: 'AND|OR|NOT|NAND', notes?: str, composite_id?: uuid, quote?: str}`
  - Creates multiple edges with shared composite_id, logic_type, notes, quote
  - Min 2 source nodes required
  - Quote field: optional excerpt from source node (max 500 chars for fair use commentary)
- Returns 201 (single): `{data: {id: uuid}, ...}`
- Returns 201 (compound): `{data: {composite_id: uuid}, ...}`

**PATCH /connections/{connection_id}/** - Update connection
- Auth: Required
- Guards: Ownership check, time window check
- URL param: `connection_id` can be individual edge ID or composite_id
  - Composite_id updates entire group (synchronized metadata)
- Body: `{notes?: str, logic_type?: str, quote?: str}` (dynamic, quote max 500 chars)
- Returns: `{data: {id: uuid, updated: true}, ...}`

**DELETE /connections/{connection_id}/** - Delete connection
- Auth: Required
- Guards: Same as PATCH
- URL param: Individual edge ID or composite_id
  - Composite_id deletes entire group
- Returns: `{data: {id: uuid, deleted: true}, ...}`

#### Graph Operations

**GET /graph/** - Full graph export
- Auth: None
- Returns: `{data: {claims: [...], sources: [...], edges: [...]}, ...}`
- Format: Raw AGE format for frontend Cytoscape conversion
- Note: Currently inefficient (queries each node for connections), see TODO comment (graph/views.py:591)

**GET /search/?q={query}&type={claim|source}** - Search nodes
- Auth: None
- Query params:
  - `q` (required): Search query string
  - `type` (optional): Filter by node type
- Uses: Django full-text search (SearchService, Phase 3)
- Returns: `{data: {results: [...]}, meta: {source: 'django'}, ...}`

#### Engagement & Analytics

**POST /pageview/{entity_id}/** - Track page view
- Auth: None (AllowAny, GDPR-compliant - no personal data)
- Body: `{entity_type: 'claim|source|connection'}`
- Returns: `{data: {count: int, created: bool}, ...}`

**GET /engagement/{entity_id}/?entity_type={type}** - Get engagement metrics
- Auth: None
- Query params: `entity_type` (required): 'claim|source|connection'
- Returns:
```json
{
  "data": {
    "engagement_score": float,
    "components": {
      "page_views": int,
      "comments": int,
      "connections": int,
      "ratings": {
        "count": int,
        "avg": float,
        "contribution": float
      }
    },
    "edit_window": {
      "max_hours": float,
      "hours_elapsed": float,
      "can_edit": bool,
      "reason": str|null
    }
  }
}
```

### Authentication & Permissions

**Pattern**: `@permission_classes([IsAuthenticatedOrReadOnly])`
- GET endpoints: Public (no auth required)
- POST/PATCH/DELETE: Authenticated users required (except anonymous creation allowed for claims/sources/connections)

**Ownership Guards** (views.py:26-44):
- `check_entity_ownership(entity_uuid, entity_type, user_id)`: Verifies user created the entity via UserAttribution table
- Applied before PATCH/DELETE operations

**Time Window Guards** (views.py:131-181):
- `check_edit_time_window(entity_uuid, entity_type)`: Engagement-adjusted edit windows
  - Grace period: First 1 hour always editable
  - Base max: 720 hours (30 days)
  - Engagement reduction: `max_hours = max(24, 720 / (1 + engagement/5))`
  - Higher engagement → shorter window (asymptotes to 24hr minimum)
- Applied before PATCH/DELETE operations

**Engagement Formula** (views.py:47-128):
```
engagement = page_views + 5*comments + 15*connections + 3*rating_count*(avg_rating - 0.5)
```

### Serializers (DRF Validation)

Located in `graph/serializers.py`:

- `ClaimCreateSerializer`: Validates claim creation (content optional)
- `SourceCreateSerializer`: Validates source creation (title required, source_type choices, JSON fields for authors/metadata)
- `ConnectionCreateSerializer`: Validates single connection (logic_type choices, quote max 500 chars)
- `CompoundConnectionCreateSerializer`: Validates compound connection (min 2 sources, required logic_type, quote max 500 chars)
- `NodeUpdateSerializer`, `EdgeUpdateSerializer`: Generic (dynamic validation in views)

**Source Type Choices**: 'journal_article', 'book', 'book_chapter', 'website', 'newspaper', 'magazine', 'conference_paper', 'thesis', 'report', 'personal_communication', 'observation', 'preprint'

**Logic Type Choices**: 'AND', 'OR', 'NOT', 'NAND'

### Frontend Integration

**Data Flow**:
1. User action (React component)
2. API call via APInterface layer
3. Django view validates request (serializer)
4. Calls `LanguageOperations` (PS_Graph_DB/src/language.py)
5. Atomic write to AGE (current graph) + Django (version log)
6. Response wrapped in `standard_response()` format
7. APInterface parses {data, meta, error} structure
8. React component updates UI

**Error Handling Pattern**:
Frontend checks `error` field in response. Common error types:
- Validation errors: `error` is object with field keys
- Duplicate detection: `error` is string starting with "duplicate_"
- Permission errors: `error` is human-readable string
- Time window: `error` contains "Edit window expired..."

### Change Checklist for API

When modifying API contracts:

- [ ] Update serializers in `graph/serializers.py` (add/modify field validation)
- [ ] Update view logic in `graph/views.py` (request handling, guards)
- [ ] Update URL patterns in `graph/urls.py` if adding new endpoints
- [ ] Update frontend APInterface calls (check error handling for new error types)
- [ ] Update this documentation section
- [ ] Test: serializer validation → view guards → language.py operations → response format