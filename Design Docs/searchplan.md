# Search & Deduplication Architecture

## Overview

Two-domain redundancy reduction system:
1. **Creation-Time Prevention** - Stop duplicates from entering the graph
2. **Post-Creation Cleanup** - User-driven merge/equivalence operations (see Fork_Merge.md)

This document covers Phase 1-2: creation-time prevention using PostgreSQL full-text search and trigram matching.

---

## Architecture Principles

### Search vs Deduplication: Different Tolerance for False Positives

| Feature | Search (User Finding Nodes) | Deduplication (Creation Validation) |
|---------|----------------------------|-------------------------------------|
| **Goal** | Cast wide net, show anything potentially relevant | Only warn when highly confident it's duplicate |
| **False Positives** | OK (user can ignore irrelevant results) | BAD (frustrates users, erodes trust) |
| **Method** | Full-text + trigrams (threshold=0.3) | Exact + trigrams (threshold=0.85+) |
| **Response** | Show results list | Block creation (409 error) |

### Node Identity & Deduplication Strategy

| Node Type | Primary Identity | Search Field | Deduplication Checks |
|-----------|-----------------|--------------|---------------------|
| **Claim** | Content | `content` (full field) | 1. Exact match (`content_normalized`)<br>2. High similarity (trigram > 0.85) |
| **Source** | URL → Title → Content | `title` (NOT content) | 1. URL exact match (`url_normalized`)<br>2. Title exact match (`title_normalized`)<br>3. Title similarity (trigram > 0.85) |

**Key Insight**: Source `content` field is user's personal summary, not searchable/deduplicatable. Title is the canonical human-readable identifier.

### Database Separation of Concerns

**AGE Graph Database** - Pure topology only:
- Graph structure (nodes, edges, traversal)
- Create/update/delete operations
- Topological queries (connections, paths)

**Django Relational Database** - All attribute-based queries:
- Search (full-text, substring, metadata)
- Deduplication (exact match, similarity)
- Filtering, aggregation, temporal reconstruction

**Principle**: If it doesn't traverse edges, it doesn't belong in AGE.

---

## Technical Stack

### PostgreSQL Extensions
```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- Trigram matching
-- Full-text search is built-in via to_tsvector()
```

### Search Technologies

#### Full-Text Search (PostgreSQL Built-in)
```sql
-- Tokenization, stemming, stop word removal
to_tsvector('english', 'running shoes') @@ to_tsquery('english', 'run & shoe')
-- Matches: "running" → "run", automatically ignores "the", "a", etc.
```

**Benefits**:
- Handles word variations ("running" = "run")
- Relevance ranking via `ts_rank()`
- Fast (GIN indexed)

**Limitations**:
- Won't match synonyms ("climate change" ≠ "global warming")

#### Trigram Matching (pg_trgm Extension)
```sql
-- Character n-gram overlap
similarity('climate change', 'climat change')  -- 0.96 (typo)
similarity('climate change', 'climate crisis')  -- ~0.5 (partial overlap)
```

**Benefits**:
- Typo tolerance
- Partial word matches
- Works with any language

**Use Cases**:
- Search: Low threshold (0.3) for broad matching
- Deduplication: High threshold (0.85+) for confident duplicates

---

## Implementation

### Backend Architecture

#### Use Bookkeeper Tables for Search/Deduplication

**Rationale**: `ClaimVersion` / `SourceVersion` already track all node state. No need for separate mirror tables.

**Current version query pattern**: `WHERE valid_to IS NULL`

#### Enhanced Bookkeeper Models
Extra fields="read optimization tradeoff"
```python
# backend/PS_Django_DB/bookkeeper/models.py

class ClaimVersion(models.Model):
    # Existing fields
    node_id = models.UUIDField(db_index=True)
    content = models.TextField()
    operation = models.CharField(max_length=10)  # CREATE, UPDATE, DELETE
    valid_from = models.DateTimeField(db_index=True)
    valid_to = models.DateTimeField(null=True, blank=True, db_index=True)

    # NEW: Search optimization
    content_search = SearchVectorField(null=True)  # Auto-populated via trigger
    content_normalized = models.TextField(db_index=True, null=True)  # For exact duplicate detection

    class Meta:
        indexes = [
            models.Index(fields=['node_id', 'valid_to']),  # Current version lookups
            GinIndex(fields=['content_search']),  # Full-text search
            GinIndex(fields=['content'], opclasses=['gin_trgm_ops']),  # Trigram similarity
        ]

class SourceVersion(models.Model):
    # Existing fields
    node_id = models.UUIDField(db_index=True)
    content = models.TextField()  # User's summary/notes (not searched)
    url = models.URLField(null=True, blank=True)
    title = models.TextField(null=False, blank=False)  # REQUIRED - primary searchable field
    author = models.TextField(null=True, blank=True)
    operation = models.CharField(max_length=10)
    valid_from = models.DateTimeField(db_index=True)
    valid_to = models.DateTimeField(null=True, blank=True, db_index=True)

    # NEW: Search + deduplication (TITLE-based, not content)
    title_search = SearchVectorField(null=True)  # Full-text search on title
    title_normalized = models.TextField(db_index=True, null=True)  # Exact duplicate detection
    url_normalized = models.CharField(max_length=2048, null=True, db_index=True)  # Canonical URL

    class Meta:
        indexes = [
            models.Index(fields=['node_id', 'valid_to']),
            models.Index(fields=['url_normalized']),  # URL deduplication (primary)
            GinIndex(fields=['title_search']),  # Full-text search on title
            GinIndex(fields=['title'], opclasses=['gin_trgm_ops']),  # Trigram similarity on title
        ]
```

**Auto-update triggers** (created via migration):
```sql
-- Claim: index content field
CREATE TRIGGER claim_version_search_update
BEFORE INSERT OR UPDATE ON bookkeeper_claimversion
FOR EACH ROW EXECUTE FUNCTION
tsvector_update_trigger(content_search, 'pg_catalog.english', content);

-- Source: index TITLE field (not content)
CREATE TRIGGER source_version_title_search_update
BEFORE INSERT OR UPDATE ON bookkeeper_sourceversion
FOR EACH ROW EXECUTE FUNCTION
tsvector_update_trigger(title_search, 'pg_catalog.english', title);
```

---

### Normalization Functions

#### URL Normalization (Strict)
```python
# backend/PS_Django_DB/graph/utils.py

def normalize_url(url: str) -> str | None:
    """
    Canonical URL form for duplicate detection.

    Examples:
        'HTTPS://WWW.Example.com/Article/' -> 'example.com/article'
        'http://example.com/page?utm=fb' -> 'example.com/page'

    Rules:
        - Lowercase
        - Remove protocol (http/https)
        - Remove www prefix
        - Remove trailing slashes
        - Remove query params (optional - configure based on source needs)
        - Remove fragments (#anchors)
    """
    if not url or not url.strip():
        return None

    url = url.strip().lower()

    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    parsed = urlparse(url)
    domain = parsed.netloc.replace('www.', '')
    path = parsed.path.rstrip('/')

    return f"{domain}{path}"
```

#### Content Normalization (For Exact Matching)
```python
def normalize_content(content: str) -> str:
    """
    Canonical content form for exact duplicate detection.

    Rules:
        - Lowercase
        - Trim whitespace
        - Collapse multiple spaces to single space
    """
    import re
    return re.sub(r'\s+', ' ', content.strip().lower())
```

---

### Search Service

```python
# backend/PS_Django_DB/graph/services.py

class SearchService:
    @staticmethod
    def search_nodes(query: str, node_type: str = None) -> list:
        """
        Search current node versions using full-text + trigram.

        Args:
            query: Search string
            node_type: 'claim' | 'source' | None (both)

        Returns:
            List of {id, node_type, content/title, url?}
        """
        # Queries ClaimVersion/SourceVersion with valid_to IS NULL
        # For claims: searches content field
        # For sources: searches TITLE field (not content)
        # Combines full-text rank + trigram similarity
        # Low threshold (0.3) for broad search results

class DeduplicationService:
    @staticmethod
    def check_duplicate_claim(content: str) -> dict | None:
        """
        Duplicate detection for claims.

        Args:
            content: Claim content to check

        Returns:
            {
                'duplicate_type': 'exact' | 'similar',
                'existing_id': UUID,
                'existing_content': str,
                'similarity_score': float  # For 'similar' type
            } or None

        Matching strategy:
            1. Exact match on content_normalized (highest priority)
            2. Trigram similarity > 0.85 (typos, minor variations)
        """

    @staticmethod
    def check_duplicate_source(url: str, title: str) -> dict | None:
        """
        Three-tier source deduplication.

        Args:
            url: Source URL (optional but recommended)
            title: Source title (required)

        Returns:
            {
                'duplicate_type': 'url' | 'title_exact' | 'title_similar',
                'existing_id': UUID,
                'existing_title': str,
                'existing_url': str,
                'similarity_score': float  # For 'title_similar'
            } or None

        Matching strategy:
            1. URL normalized match (hard block - same document)
            2. Title exact match on title_normalized
            3. Title trigram similarity > 0.85 (catches typos like "IPCC 2021" vs "IPCC Report 2021")

        Note: Source content field is NOT checked - it's user's personal summary.
        """
```

---

### API Integration

#### Remove from language.py
```python
# DELETE: backend/PS_Graph_DB/src/language.py lines 358-413
# search_nodes() method - moving to Django
```

AGE layer should only handle:
- Graph mutations (create/edit/delete)
- Topological queries (get connections, traverse edges)
- Full graph retrieval for visualization

#### Django API Views

```python
# backend/PS_Django_DB/graph/views.py

@api_view(['GET'])
@permission_classes([AllowAny])
def search_nodes(request):
    """
    GET /api/nodes/search?q=climate&type=claim

    Returns: {
        data: {
            results: [
                {id: UUID, node_type: 'claim', content: '...'},
                ...
            ]
        },
        meta: {timestamp, source: 'django'},
        error: null
    }
    """

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_claim(request):
    """
    POST /api/claims/create
    Body: {content: '...'}

    Steps:
        1. Check DeduplicationService.check_duplicate_claim()
        2. If exact/similar duplicate: return 409 Conflict with existing node info
        3. If no duplicate: create via LanguageOperations (writes to AGE + bookkeeper)

    Returns:
        - 201 Created: {data: {uuid, content}}
        - 409 Conflict: {
            error: 'duplicate_exact' | 'duplicate_similar',
            data: {existing_node_id, existing_content, similarity_score?}
          }
    """

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_source(request):
    """
    POST /api/sources/create
    Body: {title: '...', url: '...', content: '...', ...}

    Steps:
        1. Validate title is present (required field)
        2. Check URL duplicate (if URL provided - strict block)
        3. Check title duplicate (exact + similarity)
        4. Create if no duplicates

    Returns:
        - 201 Created: {data: {uuid, title, url}}
        - 400 Bad Request: {error: 'title_required'}
        - 409 Conflict: {
            error: 'duplicate_url' | 'duplicate_title_exact' | 'duplicate_title_similar',
            data: {existing_node_id, existing_title, existing_url?, similarity_score?}
          }
    """
```

---

### Frontend Integration

#### SearchBar Component (Already Exists)
```javascript
// frontend/components/common/SearchBar.jsx

// Current: calls searchNodes(query, nodeTypeFilter)
// Backend endpoint: GET /api/nodes/search?q=...&type=...

// Uses full-text + trigram search (broad threshold)
// Shows results dropdown with node type badges
```

#### NodeCreationModal Updates
```javascript
// frontend/components/graph/NodeCreationModal.jsx

const handleCreate = async () => {
    // Validation
    if (nodeType === 'source' && !title.trim()) {
        setError('Source title is required');
        return;
    }

    // Attempt creation
    const result = nodeType === 'claim'
        ? await createClaim(token, {content})
        : await createSource(token, {title, url, content, author});

    // Handle duplicate errors - CLAIMS
    if (result.error === 'duplicate_exact' || result.error === 'duplicate_similar') {
        const label = result.error === 'duplicate_exact' ? 'already exists' : 'is very similar to an existing claim';
        setError(
            <div className="duplicate-error">
                <strong>This claim {label}</strong>
                <p>{result.data.existing_content?.slice(0, 100)}...</p>
                {result.data.similarity_score && (
                    <small>Similarity: {(result.data.similarity_score * 100).toFixed(0)}%</small>
                )}
                <a href={`/context?id=${result.data.existing_node_id}`} target="_blank">
                    View existing claim →
                </a>
            </div>
        );
        return; // Block creation
    }

    // Handle duplicate errors - SOURCES
    if (result.error === 'duplicate_url') {
        setError(
            <div className="duplicate-error">
                <strong>This URL already exists</strong>
                <p><em>{result.data.existing_title}</em></p>
                <a href={`/context?id=${result.data.existing_node_id}`} target="_blank">
                    View existing source →
                </a>
            </div>
        );
        return;
    }

    if (result.error === 'duplicate_title_exact' || result.error === 'duplicate_title_similar') {
        const label = result.error === 'duplicate_title_exact'
            ? 'A source with this title already exists'
            : 'A source with a very similar title exists';
        setError(
            <div className="duplicate-error">
                <strong>{label}</strong>
                <p><em>{result.data.existing_title}</em></p>
                {result.data.similarity_score && (
                    <small>Similarity: {(result.data.similarity_score * 100).toFixed(0)}%</small>
                )}
                <a href={`/context?id=${result.data.existing_node_id}`} target="_blank">
                    View existing source →
                </a>
            </div>
        );
        return;
    }

    // ... proceed with successful creation ...
}
```

---

## Phased Implementation

### Phase 0: Mandatory Source Title Field
**Impact**: Enables title-based deduplication, improves source identity
**Why First**: URL + Title deduplication is more valuable than content similarity. Get the data model right before building search infrastructure.

#### Backend Changes

1. **Migration**: Make `SourceVersion.title` non-nullable for new entries
```python
# backend/PS_Django_DB/bookkeeper/migrations/XXXX_require_source_title.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('bookkeeper', 'XXXX_previous_migration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sourceversion',
            name='title',
            field=models.TextField(null=False, blank=False),
        ),
    ]
```

2. **Validation**: Update source creation endpoint
```python
# backend/PS_Django_DB/graph/views.py
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_source(request):
    title = request.data.get('title', '').strip()
    if not title:
        return Response(
            {'error': 'title_required', 'message': 'Source title is required'},
            status=400
        )
    # ... rest of creation logic
```

#### Frontend Changes

**NodeCreationModal.jsx** - Update source form validation:
```javascript
const handleCreate = async () => {
    if (nodeType === 'source') {
        if (!title.trim()) {
            setError('Source title is required');
            return;
        }
    }
    // ... proceed with creation
}

// Update form UI - add asterisk and required styling
<input
    type="text"
    placeholder="Source title *"  // Add asterisk
    value={title}
    onChange={(e) => setTitle(e.target.value)}
    required
    className={!title.trim() ? 'input-error' : ''}
/>
```

#### Data Backfill (If Needed)

If existing sources have null titles:
```python
# Django shell - one-time script
from bookkeeper.models import SourceVersion

for source in SourceVersion.objects.filter(title__isnull=True):
    # Option A: Use first N chars of content
    source.title = source.content[:100] + '...' if len(source.content) > 100 else source.content

    # Option B: Use URL domain if available
    # from urllib.parse import urlparse
    # source.title = f"Source from {urlparse(source.url).netloc}" if source.url else "Untitled Source"

    source.save()
```

**Test**:
1. Try creating source without title → Should show validation error
2. Fill title, submit → Should create successfully
3. Check database → `title` field populated for new entries

---

### Phase 1: URL Deduplication
**Impact**: Prevents duplicate sources via URL

1. Add `url_normalized` field to `SourceVersion`
2. Create `normalize_url()` utility in `graph/utils.py`
3. Add index on `url_normalized`
4. Update `create_source` view to check duplicates via `DeduplicationService`
5. Frontend handles 409 error response

**Test**: Try creating source with URLs:
- `https://example.com/article`
- `http://www.example.com/article/`
- Should detect as duplicate

---

### Phase 2: Title & Content Duplicate Detection
**Impact**: Prevents duplicate claims (via content) and sources (via title)

1. Add search fields to bookkeeper models:
   - Claims: `content_search`, `content_normalized`
   - Sources: `title_search`, `title_normalized`
2. Create migration with GIN indexes + triggers
3. Implement `DeduplicationService.check_duplicate_claim()` and `check_duplicate_source()`
4. Update `create_claim` / `create_source` views
5. Frontend error handling for all duplicate types

**Test Claims**:
- "Climate change causes sea level rise"
- "climate  change   causes sea level rise" (whitespace)
- "Climate change cause sea level rise" (typo)
- Should detect first two as exact, third as similar (>0.85)

**Test Sources**:
- Title: "IPCC 2021 Report"
- Title: "IPCC Report 2021" (similar)
- Should detect as `duplicate_title_similar`

---

### Phase 3: Full-Text Search
**Impact**: Better search UX, replaces substring matching

1. Implement `SearchService.search_nodes()`
   - Claims: search on `content_search` field
   - Sources: search on `title_search` field
2. Remove `search_nodes()` from `language.py` (line ~358-413)
3. Update Django API view to use `SearchService`
4. Frontend `SearchBar.jsx` uses new endpoint

**Test**:
- Search for "climate" - should match claim content "Climate change causes..."
- Search for "IPCC" - should match source titles "IPCC 2021 Report"

### Phase 4 (Future): Semantic Embeddings
**Effort**: 1-2 days
**When**: After >1000 nodes, if users report missed duplicates

Requires ML infrastructure (sentence transformers, pgvector extension).
Catches semantic similarity that trigrams miss ("climate change" ≈ "global warming").

---

## Migration Strategy

### 1. Enable PostgreSQL Extension
```bash
cd backend/PS_Django_DB
uv run python manage.py dbshell
```
```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

### 2. Create Migration
```bash
uv run python manage.py makemigrations bookkeeper
uv run python manage.py migrate
```

### 3. Backfill Existing Data
```python
# Django shell
from bookkeeper.models import ClaimVersion, SourceVersion
from graph.utils import normalize_url, normalize_content

# Normalize existing claim content
for claim in ClaimVersion.objects.filter(content_normalized__isnull=True):
    claim.content_normalized = normalize_content(claim.content)
    claim.save()

# Normalize existing source titles + URLs (NOT content)
for source in SourceVersion.objects.all():
    if source.title and not source.title_normalized:
        source.title_normalized = normalize_content(source.title)
    if source.url and not source.url_normalized:
        source.url_normalized = normalize_url(source.url)
    source.save()
```

---

## Bonus: Temporal Search

Since we're querying bookkeeper, temporal search comes free:

```python
def search_nodes_at_timestamp(query: str, timestamp: datetime):
    """Search graph as it existed at timestamp T"""
    return ClaimVersion.objects.filter(
        valid_from__lte=timestamp,
        Q(valid_to__gt=timestamp) | Q(valid_to__isnull=True)
    ).filter(content__icontains=query)
```

Aligns with temporal reconstruction architecture in Temporality.md.

---

## Performance Considerations

### Index Sizes
- Full-text index (`content_search`): ~30-50% of content size
- Trigram index: ~200-300% of content size (larger but enables fuzzy matching)
- Normalized fields: ~100% of content size

**Estimate for 10k nodes**:
- Content: ~1MB (100 chars avg)
- Indexes: ~4-5MB total
- Acceptable overhead for <100k nodes

### Query Performance
- Exact match (normalized): O(1) via index
- Full-text search: O(log n) via GIN index
- Trigram similarity: O(n) worst case, but GIN index makes it practical for <100k rows

**Optimization**: If trigram queries get slow (>1s), add materialized view with pre-computed similarity scores.

---

## Future Enhancements

### Search Sidebar for Graph Page
```
GraphPage
├─ Cytoscape visualization (main area)
└─ SearchSidebar (collapsible panel)
   ├─ Search input
   ├─ Results list
   └─ "Create new node" button (if no results)
```

**Purpose**: Let users browse existing nodes before creating duplicates.

**When**: After basic deduplication is proven, before modal redesign.

### Search-First Modal
Convert `NodeCreationModal` to default to search:
```
NodeConnectionModal (renamed)
├─ Search Tab (default)
│  ├─ Search existing nodes
│  └─ Click to connect (skips creation)
└─ Create Tab (fallback)
   └─ Current creation form
```

**When**: After graph reaches critical mass (~500+ nodes).

### Synonym Expansion
Manually curated synonym dictionary:
```python
synonyms = {
    'climate change': ['global warming', 'climate crisis'],
    'covid': ['coronavirus', 'sars-cov-2', 'pandemic']
}
```

**When**: If users request, domain-specific needs emerge.

---

## References

- **Fork_Merge.md**: Post-creation cleanup (merge, equivalence operations)
- **Temporality.md**: Bookkeeper version tables, temporal reconstruction
- **data_cont.md**: AGE schema, change checklist
- **PostgreSQL Full-Text Search**: https://www.postgresql.org/docs/current/textsearch.html
- **pg_trgm Extension**: https://www.postgresql.org/docs/current/pgtrgm.html
