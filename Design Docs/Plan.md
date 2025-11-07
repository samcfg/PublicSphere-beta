# Production Readiness Plan

## Phase 1: Users & Privacy
**Goal:** GDPR-compatible (no banner!!) identity system with attribution tracking. User accounts link to contributions indirectly via UserAttribution table. Foundation for social features and moderation.
  
### Django Models
- **users/models.py**: User management app
  - `User`: Extend `AbstractUser` (username, email, password, is_staff, is_superuser for admin flags)
  - `UserProfile`: Reputation and profile data (FK to User)
    - Fields: bio, display_name, total_claims, total_sources, total_connections, reputation_score, last_updated
    - Reputation calculation: contribution count only (ratings deferred to Phase 2)
  - `UserAttribution`: Links entity UUIDs to users with privacy controls
    - Fields: entity_uuid (CharField, indexed), user_id (FK to User), is_anonymous (BooleanField), entity_type (CharField: 'claim'|'source'|'connection'), timestamp (DateTimeField, auto)
    - Indexes: entity_uuid (primary lookup), user_id (user contribution queries)
    - Queried by UI to display authorship (respects is_anonymous flag)
- **bookkeeper/models.py**: Add `created_by_user_id` FK to temporal models
  - ClaimVersion, SourceVersion, ConnectionVersion get `created_by_user_id` (FK to User, nullable)
  - Graph DB stores no user data—all user→contribution mapping in Django
- **bookkeeper/admin.py**: Protect version history from admin modification
  - Override `has_delete_permission()` → False (versions immutable, append-only log)
  - Override `has_add_permission()` → False (versions only created via logging.py)
  - Admins have read-only access to complete audit trail

### Backend Operations
- **language.py**: Add `user_id` parameter to create/edit/delete operations, pass to logging
- **logging.py**: Accept `user_id`, write to version records AND create UserAttribution entry
  - On CREATE: log version with `created_by_user_id`, create UserAttribution(entity_uuid, user_id, is_anonymous, entity_type)
  - On UPDATE/DELETE: log version with `created_by_user_id` (UserAttribution unchanged—tracks original creator)
- **users/services.py**: Query contributions and compute reputation
  - `get_user_contributions(user_id)`: Query UserAttribution → fetch graph entities
  - `update_reputation(user_id)`: Recalculate metrics (total contributions by type) → update UserProfile
  - `toggle_anonymity(user_id, entity_uuid)`: Update UserAttribution.is_anonymous (retroactive)
  - `delete_account(user_id)`: Soft delete—nullify user_id in UserAttribution, delete User/UserProfile (contributions remain public, attributed as [deleted])

### Authentication & Privacy
- **users/views.py**: Registration, login, logout (session-based)
  - Password reset deferred to Phase 4 (requires email service)
- **users/serializers.py**: DRF serializers
- **settings.py**: Configure DRF, CORS, secure session cookies
  - GDPR compliance: no third-party analytics, session/CSRF cookies only
  - IP hashing: ephemeral hash at login/registration for ban evasion check (not stored beyond Ban table, 30 days)
  - Password hashing: Django defaults (PBKDF2)

### Testing
- **test_data.py**: Generate test users with contributions, test attribution queries via DRF API
- Test anonymity toggle, account deletion (soft delete), reputation calculation
- Test API endpoints via Django test client or curl

**Note:** Frontend integration (UI elements) deferred to Phase 3

---

## Phase 2: Social Features
**Goal:** Ratings, comments, and moderation tools. No graph DB changes—all Django.

### Django Models
- **social/models.py**: Social interaction layer
  - `Rating`: user_id (FK), entity_uuid (CharField), entity_type (CharField: 'claim'|'source'|'connection'), score (FloatField 0-100), dimension (CharField: 'confidence'|'relevance'), timestamp (DateTimeField)
    - Indexes: entity_uuid, user_id, (entity_uuid, user_id) unique constraint
  - `Comment`: user_id (FK), entity_uuid (CharField), entity_type (CharField), content (TextField), parent_comment_id (FK self, nullable), is_deleted (BooleanField soft delete), timestamp (DateTimeField)
    - Indexes: entity_uuid, user_id, parent_comment_id
- **bookkeeper/models.py**: Temporal versions for social data
  - `RatingVersion`: Tracks rating changes (score edits, deletions)
  - `CommentVersion`: Tracks comment edits/deletions (preserves deleted content in audit trail)

### Backend Operations
- **social/services.py**: Social interaction operations (business logic layer)
  - `rate_entity(user_id, entity_uuid, score, dimension)`: Create/update rating
  - `comment_on_entity(user_id, entity_uuid, content, parent_id)`: Create comment
  - `get_entity_ratings(entity_uuid)`: Aggregate ratings (avg, count, distribution)
  - `get_entity_comments(entity_uuid)`: Fetch comment tree (respect is_deleted)
  - `delete_comment(user_id, comment_id)`: Soft delete (user or admin)
  - Aggregation: controversial entities (high rating variance), cache in Redis
  - `flag_entity(admin_id, entity_uuid, reason)`: Mark for review
  - `hide_entity(admin_id, entity_uuid)`: Soft-hide from UI (graph entity remains, UI filters it out)
  - `verify_source(admin_id, source_uuid)`: Mark source as verified (stored in Source properties via language.py edit)
- **users/services.py**: Update reputation calculation
  - Extend `update_reputation()` to include avg ratings received on user's contributions

### DRF API Layer
- **social/serializers.py**: DRF serializers for input validation
  - `RatingSerializer`: Validate score (0-100), dimension (confidence|relevance), entity_uuid, entity_type
  - `RatingCreateSerializer`: For creating new ratings
  - `CommentSerializer`: Validate content length, entity_uuid, entity_type, parent_comment_id
  - `CommentCreateSerializer`: For creating new comments
  - `FlagSerializer`: For moderation flags (reason, entity_uuid)
- **social/views.py**: DRF API views wrapping services.py
  - `rate_entity()` - POST/PATCH rating (auth required)
  - `entity_ratings()` - GET aggregated ratings for entity (public)
  - `comment_entity()` - POST comment (auth required)
  - `entity_comments()` - GET comment tree for entity (public, filters soft-deleted)
  - `comment_detail()` - PATCH/DELETE comment (auth required, own comments only)
  - `flag_entity()` - POST moderation flag (moderator/admin only)
  - Standard response format: `{data, meta, error}`
- **social/urls.py**: URL routing
  - `/api/social/ratings/` - POST rating
  - `/api/social/ratings/?entity=<uuid>` - GET ratings for entity
  - `/api/social/comments/` - POST comment
  - `/api/social/comments/?entity=<uuid>` - GET comments for entity
  - `/api/social/comments/<id>/` - PATCH/DELETE comment
  - `/api/social/moderation/flag/` - POST flag
- **config/urls.py**: Wire social app
  - `path('api/social/', include('social.urls'))`

### Moderation Tools
- **social/admin.py**: Custom Django admin and moderator groups with custom actions
  - Flag content for review, soft-delete comments, view flagged entities
  - Read-only access to version history (RatingVersion, CommentVersion protected like bookkeeper versions)
  - Custom admin actions for bulk moderation

### Temporal Logging
- **logging.py**: Log rating/comment versions via existing temporal infrastructure

### Testing
- **test_data.py**: Generate ratings/comments, test aggregation performance, moderation workflows
- Test API endpoints via Django test client or curl
- Test moderation permissions (moderator vs admin vs user)

**Note:** Frontend integration (rating widgets, comment UI) deferred to Phase 3

---

## Phase 3: Security Hardening & API Layer
**Goal:** Consolidate to Django REST API. Protect against attacks. Validate inputs. Harden attack surface.

### API Architecture Migration
- **Consolidate to pure Django:** Replace Node.js/Express with Django REST Framework (DRF)
  - Single Python stack reduces maintenance burden (one runtime, one dependency system)
  - Direct function calls to `language.py` (no IPC overhead from Node→Python communication)
  - Django already required for users/temporal—serves static files + API from one process
- **Resource-based REST API structure:** Organized by domain entities, not page contexts
  - `/api/claims/` - List all claims (GET), create claim (POST)
  - `/api/claims/:uuid` - Get/update/delete specific claim (GET/PATCH/DELETE)
  - `/api/claims/:uuid/connections` - Get claim's connections
  - `/api/sources/` - List all sources, create source
  - `/api/sources/:uuid` - Get/update/delete specific source
  - `/api/connections/` - Create connection between entities
  - `/api/connections/:uuid` - Get/update/delete connection (supports composite_id for compound edges)
  - `/api/users/:username` - User profile
  - `/api/users/:username/contributions` - User's claims/sources/connections
  - `/api/comments?entity=:uuid` - Comments on any entity (claim/source/connection)
  - `/api/ratings?entity=:uuid` - Ratings on any entity
  - `/api/temporal/snapshot?timestamp=ISO` - Historical graph state
- **graph/ Django app:** DRF views wrapping `language.py` operations
  - `views.py`: Import `LanguageOperations`, call methods directly (e.g., `ops.create_claim()`)
  - `serializers.py`: Validate claim/source/connection input (DRF serializers)
  - `urls.py`: Define `/api/claims/*`, `/api/sources/*`, `/api/connections/*` routes
- **Response format standardization**: JSON envelope across all endpoints
  - `{data: {}, meta: {timestamp, source}, error: null | {code, message}}`
  - Consistent error handling for frontend (HTTP status codes + structured messages)
- **Frontend integration:** Django serves static files from `static/` directory
  - Move `age-cytoscape-api/index.html` and `src/*.js` to Django `static/`
  - Update `src/api.js` baseURL to `/api/claims`, `/api/sources`, etc.
  - `formatForCytoscape()` logic moves to Django view (Python equivalent of `database.js`)
- **Authentication**: Session-based auth via Django sessions (built-in)
- **CORS**: Not needed (same-origin: frontend served from Django, API on same domain)

### Input Validation
- **language.py**: Validate UUIDs, content lengths, allowed characters; sanitize XSS
- **schema.py**: Add validation rules (max lengths, regex patterns, enums for logic_type/source_type)
- **social/services.py**: Sanitize comment/rating content (XSS prevention, length limits)

### API Security
- **Django middleware**: Rate limiting (django-ratelimit per-user/IP), CSRF protection (built-in), request size limits
- **settings.py**: Production security settings
  - `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS`
  - `ALLOWED_HOSTS`, `SECURE_CONTENT_TYPE_NOSNIFF`, `X_FRAME_OPTIONS`
  - No CORS needed (same-origin architecture)
- **DRF permissions**: Require authentication for write operations, throttling classes for rate limiting

### Database Security
- **database.py**: Verify parameterized queries (already using psycopg2 parameters), connection pooling
- **settings.py**: Separate database users (read-only for temporal queries, write for graph operations)
- Query timeout already implemented (30s in database.py)

### Dependency Security
- **requirements.txt**: Pin versions, run `pip-audit` for known vulnerabilities
- **Frontend dependencies**: Cytoscape.js loaded via CDN (version pinned in index.html script tags)
- Consider: SCA tool (Snyk/Dependabot), SAST scan (Bandit for Python)

### Infrastructure Security
- Cloudflare free tier for DDoS mitigation (DNS proxy)
- Ban evasion: ephemeral IP hash at login/registration checked against Ban table (already in Phase 1)

### Deployment Infrastructure
- **Dockerfile**: Multi-stage build (Python dependencies + static files collection)
  - Base: python:3.11-slim (minimal attack surface)
  - Install Python dependencies from requirements.txt
  - Copy Django project + PS_Graph_DB modules
  - Run `collectstatic` to gather frontend files into Django static directory
  - Non-root user for runtime security
- **docker-compose.yml**: Local development stack
  - PostgreSQL container with AGE extension
  - Django container (serves API + static files on port 8000)
  - Shared network, volume for database persistence
- **.dockerignore**: Exclude `__pycache__`, `.git`, `test files`, `*.pyc`, `.venv`
- **Environment variables**: DB credentials, `SECRET_KEY`, `ALLOWED_HOSTS`, SendGrid key (Phase 4)
- **Production deployment**: Two containers (PostgreSQL + Django), reverse proxy (Nginx) for static file caching/SSL termination

### Testing
- **tests/security/**: Injection attacks (SQL, Cypher, XSS), CSRF bypass attempts, rate limit validation, input boundary tests
- **tests/docker/**: Container build validation, environment variable injection, inter-service communication

## Phase 4: Frontend Maturity
**Goal:** Polish UI, optimize performance, add context navigation, enable email notifications.

### Email Service
- **settings.py**: Configure SendGrid API (free tier: 100 emails/day)
  - EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
  - SENDGRID_API_KEY from environment variable
- **users/views.py**: Add password reset flow (PasswordResetView, PasswordResetConfirmView)
- **templates/**: Password reset email templates (HTML + plain text)
- **Future**: Email notifications for comments/replies (opt-in via UserProfile)

### Context Navigation
- **graph/context_views.py**: `/api/context/conclusion/:claim_id?depth=N` endpoint—traverse backward via Cypher queries, assign coordinate labels (a1, b2ca1), return subgraph
- **graph.js**: Context mode—toggle full graph vs focused view, display coordinates, depth controls

### Performance
- **graph.js**: Lazy loading (viewport culling), web workers for layout, canvas vs SVG comparison
- **graph/views.py**: Redis caching for expensive queries, ETags for conditional requests, pagination for large result sets
- **language.py**: Traversal depth limits in Cypher queries, query optimization

### UI/UX
- **index.html**: Responsive CSS, accessibility (ARIA, keyboard nav), dark mode
- **graph.js**: Smooth animations, multi-select, undo/redo, minimap, subgraph export, graph diffing
- **Future**: Collaborative editing (Django Channels for WebSockets, CRDT conflict resolution)

### Error Handling
- **graph/views.py**: DRF exception handlers for standardized error responses (HTTP codes, messages)
- **graph.js**: Graceful degradation, retry logic with exponential backoff

### Documentation
- **docs/**: User guide (create claims, ratings, privacy), developer docs (API ref, architecture diagrams)

### Testing
- **tests/e2e/**: Playwright/Cypress workflows, cross-browser, performance benchmarks

---

## Cross-Cutting Concerns

### Data Integrity
- **schema.py**: Constraint validation (unique usernames, valid emails, no dangling edges)
- **language.py**: Transaction retry logic, optimistic locking

### Migration Strategy
- **migrations/**: Django migrations (temporal), graph schema versioning (custom script)
- **rollback.py**: Revert schema changes, restore from temporal snapshot

### Backups
- **backup.sh**: PostgreSQL dumps (AGE + Django), S3/local storage, point-in-time recovery testing
- **cron**: Daily backups

### Monitoring & Logging
- **logging.py**: Structured JSON logging, log levels, rotation
- **monitoring/**: Prometheus metrics, Grafana dashboards, alerting

### Rate Limiting
- **rate_limit.py**: Per-user (claims/hour), per-IP (requests/minute), configurable thresholds

---

## File Change Summary by Phase

### Phase 1: Users & Privacy
- **Modify:**
  - bookkeeper/models.py (add created_by_user_id to version models)
  - bookkeeper/admin.py (read-only version protection)
  - language.py (add user_id parameter)
  - logging.py (accept user_id, create UserAttribution)
  - test_data.py (generate users, test attribution via DRF API)
  - settings.py (DRF, CORS, GDPR settings)
  - config/urls.py (add users/ app routes)
- **Create:**
  - users/ Django app (models.py with User/UserProfile/UserAttribution, services.py for business logic)
  - users/views.py (DRF API views: register, login, logout, profile, contributions, toggle_anonymity)
  - users/serializers.py (DRF serializers for input validation)
  - users/urls.py (URL routing: /api/users/*)
  - migrations for users and bookkeeper changes
- **No schema.py changes:** Graph DB remains user-agnostic
- **Note:** Frontend integration deferred to Phase 3

### Phase 2: Social Features
- **Modify:**
  - bookkeeper/models.py (add RatingVersion, CommentVersion)
  - bookkeeper/admin.py (protect rating/comment versions)
  - users/services.py (extend reputation calculation)
  - test_data.py (generate ratings/comments, test via DRF API)
  - settings.py (add social app to INSTALLED_APPS)
  - config/urls.py (add social/ app routes)
- **Create:**
  - social/ Django app (models.py with Rating/Comment, services.py for business logic, admin.py for moderation)
  - social/views.py (DRF API views: rate_entity, entity_ratings, comment_entity, entity_comments, comment_detail, flag_entity)
  - social/serializers.py (DRF serializers: RatingSerializer, CommentSerializer, FlagSerializer)
  - social/urls.py (URL routing: /api/social/*)
  - migrations for social models
- **No schema.py changes:** Social data in Django only
- **Note:** Frontend integration deferred to Phase 3

### Phase 3: Frontend Integration & Security Hardening
- **Modify:**
  - language.py (input validation, XSS sanitization)
  - schema.py (validation rules, enums)
  - database.py (verify parameterized queries, connection pooling)
  - social/services.py (sanitize comment/rating content)
  - settings.py (production security settings, static files config, security headers, separate DB users)
  - requirements.txt (pin versions, add django-ratelimit for rate limiting)
  - config/urls.py (serve index.html as main view at `/`)
- **Create:**
  - static/ directory (move age-cytoscape-api/index.html and src/*.js here)
  - static/src/data.js (add formatForCytoscape() - port from database.js)
  - static/src/api.js (update API baseURL to Django endpoints: /api/graph/, /api/users/, /api/social/)
  - static/index.html (add login/logout UI, rating widgets, comment threads, user settings)
  - static/src/graph.js (integrate user attribution display, rating visualization)
  - tests/security/ (injection, CSRF, rate limit tests)
  - tests/api/ (DRF endpoint integration tests)
  - tests/docker/ (container tests)
  - Dockerfile (multi-stage Python build)
  - docker-compose.yml (PostgreSQL + Django stack)
  - .dockerignore
- **Delete:**
  - age-cytoscape-api/server.js (replaced by Django serving static files)
  - age-cytoscape-api/database.js (formatting logic moved to frontend data.js)
  - age-cytoscape-api/package.json (Node backend no longer needed)
  - age-cytoscape-api/node_modules/ (Node backend dependencies)

### Phase 4: Frontend Maturity
- **Modify:** graph.js (lazy loading, web workers), index.html (responsive CSS, accessibility), graph/views.py (caching, pagination)
- **Create:** graph/context_views.py (context navigation endpoints), docs/, tests/e2e/, performance monitoring infrastructure

### Cross-Cutting
- **Create:** backup.sh, migrations/ versioning system, monitoring/ setup, rollback.py
- **Modify:** All logging throughout codebase
