# Future Development Plan

This document consolidates Phase 4 (Frontend Maturity) and Phase 5 (Deployment) from Plan.md. 
---

## Phase 4: Frontend Maturity
**Goal:** Make UI. 
optimize performance, add context navigation, enable email notifications.
  1. Login sidebar (enables auth for everything else)
  2. Node detail panel (container for ratings/comments)
  3. Rating widget (simpler than comments)
  4. Comments thread (most complex)
  5. Homepage (once graph interaction works)
  6. User profile (once contributions tracked)
  7. Moderation panel (last, admin-only)


### Node DOS
- https://www.npmjs.com/package/react-comments-section

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

### Moderation Audit Trail (Required Enforcement Reasons)
**Goal:** Require all admin enforcement actions to include reason text for accountability and transparency.

**Architecture:** Hybrid approach combining bulk action intermediate forms with individual edit validation.

**Models:**
- **social/models.py**: Create `ModerationLog` model
  - Fields: `admin_user` (FK to User), `target_user` (FK to User, nullable), `target_comment` (FK to Comment, nullable), `action` (CharField: 'deactivate'|'activate'|'soft_delete'|'hard_delete'|'modify_permissions'), `reason` (TextField, required), `field_changes` (JSONField for before/after state), `timestamp` (DateTimeField, auto)
  - Indexes: `admin_user`, `target_user`, `timestamp`, `action`
  - Purpose: Immutable audit log of all enforcement actions with required justification

**Admin Configuration:**
- **users/admin.py**: Override `UserAdmin` with hybrid enforcement
  - **Option B (Primary)**: Custom bulk actions with intermediate forms
    - `deactivate_users_with_reason()`: Shows intermediate page requiring reason text before deactivating
    - `activate_users_with_reason()`: Shows intermediate page for reactivation
    - Template: `admin/enforcement_reason.html` (reusable across all actions)
    - Form: `EnforcementReasonForm` with required `reason` TextField
  - **Option A (Bypass Prevention)**: Override `save_model()` to block individual edits
    - Check if `is_active` or `is_staff` changed on individual user edit
    - Raise `ValidationError` with message: "Use bulk action 'Deactivate selected users' to require reason"
    - Forces admins to use intermediate form workflow

- **social/admin.py**: Update `CommentAdmin` with required reasons
  - Replace `soft_delete_comments` action with `soft_delete_with_reason()`
  - Add `hard_delete_with_reason()` action for Staff Admins
  - Both use same intermediate form pattern as user actions

- **social/admin.py**: Update `FlaggedContentAdmin` resolution actions
  - `mark_as_reviewed`, `mark_as_action_taken`, `mark_as_dismissed` already update `resolution_notes`
  - Make `resolution_notes` required (not optional) via form validation
  - Add intermediate form for bulk resolution actions

**Shared Components:**
- **common/admin_forms.py**: Create reusable `EnforcementReasonForm`
  - Required `reason` TextField with Textarea widget
  - Hidden `_selected_action` field for bulk action IDs
  - Validation: minimum 10 characters, maximum 2000 characters

- **templates/admin/enforcement_reason.html**: Reusable intermediate page template
  - Shows list of affected items (users, comments, flags)
  - Displays form with reason textarea
  - Confirm/Cancel buttons
  - Used by all enforcement actions across users/social apps

**Workflow Example (Deactivate User):**
1. Admin selects users in list view, chooses "Deactivate selected users" from dropdown
2. Intermediate page shows: selected users, reason form (required)
3. Admin submits reason → `ModerationLog` entry created for each user → users deactivated
4. Success message shows count + truncated reason
5. If admin tries to edit individual user and uncheck `is_active` → blocked with error message

**Enforcement Actions Requiring Reasons:**
- User deactivation (`is_active` → False)
- User reactivation (`is_active` → True)
- Permission changes (`is_staff`, `is_superuser` modifications)
- Comment soft delete (`is_deleted` → True)
- Comment hard delete (deletion from database)
- Flag resolution (status changes from 'pending')

**Read-Only Audit Access:**
- **social/admin.py**: Register `ModerationLogAdmin` with read-only access
  - List view: admin, target, action, reason preview, timestamp
  - Detail view: full reason, field changes JSON
  - Permissions: `has_add_permission()` → False, `has_delete_permission()` → False
  - Available to Moderators, Staff Admins, Superusers for transparency

**Testing:**
- **tests/admin/**: Test enforcement actions require reasons
  - Verify bulk actions show intermediate form
  - Verify individual edits are blocked
  - Verify `ModerationLog` entries created correctly
  - Test form validation (empty reason, too short reason)

**File Changes:**
- **Modify:** graph.js (lazy loading, web workers), index.html (responsive CSS, accessibility), graph/views.py (caching, pagination)
- **Create:** graph/context_views.py (context navigation endpoints), docs/, tests/e2e/, performance monitoring infrastructure, social/models.py (ModerationLog), common/admin_forms.py, templates/admin/enforcement_reason.html

---

## Phase 5: Deployment
**Goal:** Deploy to Railway PaaS with Cloudflare DDoS protection. Domain: publicsphere.fyi
#### Optimize fonts
- "fonttools" can strip non-latin characters (?)
- code critical font "preload"

### Docker Containerization
- **Dockerfile**: python:3.11-slim, PostgreSQL+AGE, Django+Graph modules, non-root user, port 8000
- **docker-compose.yml**: PostgreSQL+AGE service, Django service, volumes for persistence
- **.dockerignore**: Exclude `__pycache__/`, `.git/`, test files, docs

### Railway Deployment
- **Environment Variables**: `SECRET_KEY`, `DATABASE_URL`, `ALLOWED_HOSTS`, `DEBUG=False`
- **PostgreSQL**: Install AGE extension, run migrations, create graph
- **Static Files**: Run `collectstatic` in build
- **Test**: Deploy to Railway subdomain first before adding custom domain

### Cloudflare Integration (TODO: Design decisions needed)
- **DNS**: Point publicsphere.fyi to Railway via Cloudflare proxy
- **SSL Mode**: TODO - decide Full vs Full (Strict)
- **Caching**: TODO - decide static asset caching strategy, API bypass rules
- **IP Handling**: TODO - trust `CF-Connecting-IP` header? Middleware needed?
- **Rate Limiting**: Cloudflare (volumetric) vs DRF throttling (logical abuse) - clarify division

### Django Settings for Production
- **settings.py**: Environment-based config for `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`, `DATABASES`
- Enable: `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS`
- TODO: `CSRF_TRUSTED_ORIGINS` for publicsphere.fyi
- TODO: Cloudflare IP middleware if using CF-Connecting-IP

### Testing
- Docker: Local full-stack testing
- Railway: Staging deployment, migrations, HTTPS verification
- Cloudflare: SSL chain, caching behavior, IP extraction

**File Changes:**
- **Create:** Dockerfile, docker-compose.yml, .dockerignore, docs/deployment.md, common/middleware.py (Cloudflare IP)
- **Modify:** settings.py (environment variables, production security settings)

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
