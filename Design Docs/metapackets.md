# Metadata Extraction for Source Nodes

## Purpose
Allow users to create Source nodes by providing a URL. The system fetches Open Graph metadata, displays a preview, and auto-populates the Source node fields.

## User Flow

1. **User initiates**: Clicks "Add Source" or similar action
2. **Modal appears**: URL input field prominently displayed
3. **User enters URL**: Types or pastes URL into input
4. **Fetch triggered**: On blur/submit, backend fetches metadata
5. **Preview displays**: Modal shows extracted metadata in preview card
6. **User reviews/edits**: Can modify title, description, add quote/excerpt
7. **User confirms**: Creates Source node with populated fields

## Technical Architecture

### Backend Component

**New Django REST API Endpoint**: `/api/sources/fetch-metadata/`

**Request**:
```json
POST /api/sources/fetch-metadata/
{
  "url": "https://example.com/article"
}
```

**Response**:
```json
{
  "data": {
    "url": "https://example.com/article",
    "canonical_url": "https://example.com/article",  // from og:url if different
    "title": "Article Title from og:title",
    "description": "Brief description from og:description",
    "image_url": "https://example.com/og-image.jpg",
    "site_name": "Example Site",
    "article_metadata": {
      "published_time": "2025-01-15T12:00:00Z",  // if available
      "author": "Author Name",  // if available
      "section": "Category"  // if available
    }
  },
  "meta": {
    "fetch_success": true,
    "fallback_used": false  // true if og: tags missing, used <title> etc
  },
  "error": null
}
```

**Error Response**:
```json
{
  "data": null,
  "meta": {},
  "error": {
    "code": "FETCH_FAILED",
    "message": "Could not fetch URL: connection timeout"
  }
}
```

**Implementation Requirements**:

1. **HTTP Request with User-Agent**: Some sites block scrapers without proper UA
2. **Parse HTML**: Extract `<meta>` tags from `<head>`
3. **Fallback Strategy**:
   - Try `og:title` → fall back to `<title>`
   - Try `og:description` → fall back to `<meta name="description">`
   - Try `og:image` → optional, can be null
4. **Timeout Handling**: 10 second timeout for fetch
5. **Respect robots.txt**: Check if scraping allowed (optional for v1)
6. **Security**: Validate URL format, prevent SSRF attacks (no localhost/internal IPs)

**Python Libraries**:
```python
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
```

**Pseudo-implementation**:
```python
def fetch_metadata(url):
    """
    Fetches Open Graph metadata from URL
    Returns dict with title, description, image_url, etc.
    """
    # Validate URL
    parsed = urlparse(url)
    if parsed.scheme not in ['http', 'https']:
        raise ValueError("Invalid URL scheme")

    # Fetch with timeout
    headers = {'User-Agent': 'PublicSphere/1.0 (Metadata Preview)'}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()

    # Parse HTML
    soup = BeautifulSoup(response.text, 'html.parser')

    metadata = {
        'url': url,
        'canonical_url': url,
        'title': None,
        'description': None,
        'image_url': None,
        'site_name': None
    }

    # Extract Open Graph tags
    og_tags = {
        tag.get('property', '').replace('og:', ''): tag.get('content')
        for tag in soup.find_all('meta', property=True)
        if tag.get('property', '').startswith('og:')
    }

    # Populate from og: tags
    metadata['title'] = og_tags.get('title')
    metadata['description'] = og_tags.get('description')
    metadata['image_url'] = og_tags.get('image')
    metadata['site_name'] = og_tags.get('site_name')
    metadata['canonical_url'] = og_tags.get('url', url)

    # Fallbacks if og: tags missing
    if not metadata['title']:
        title_tag = soup.find('title')
        metadata['title'] = title_tag.string if title_tag else None

    if not metadata['description']:
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        metadata['description'] = desc_tag.get('content') if desc_tag else None

    # Make image_url absolute if relative
    if metadata['image_url'] and not metadata['image_url'].startswith('http'):
        metadata['image_url'] = urljoin(url, metadata['image_url'])

    return metadata
```

**Django View** (in `backend/PS_Graph_DB/views.py` or new `metadata_views.py`):
```python
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .utils.metadata_fetcher import fetch_metadata

@api_view(['POST'])
def fetch_source_metadata(request):
    """
    Fetch Open Graph metadata for a URL
    POST /api/sources/fetch-metadata/
    """
    url = request.data.get('url')

    if not url:
        return Response({
            'data': None,
            'meta': {},
            'error': {'code': 'MISSING_URL', 'message': 'URL is required'}
        }, status=400)

    try:
        metadata = fetch_metadata(url)
        return Response({
            'data': metadata,
            'meta': {'fetch_success': True, 'fallback_used': metadata.get('fallback_used', False)},
            'error': None
        })
    except requests.exceptions.Timeout:
        return Response({
            'data': None,
            'meta': {},
            'error': {'code': 'TIMEOUT', 'message': 'URL fetch timed out'}
        }, status=408)
    except requests.exceptions.RequestException as e:
        return Response({
            'data': None,
            'meta': {},
            'error': {'code': 'FETCH_FAILED', 'message': str(e)}
        }, status=400)
    except Exception as e:
        return Response({
            'data': None,
            'meta': {},
            'error': {'code': 'INTERNAL_ERROR', 'message': 'Failed to parse metadata'}
        }, status=500)
```

**URL Registration** (in `backend/PS_Graph_DB/urls.py`):
```python
path('api/sources/fetch-metadata/', views.fetch_source_metadata, name='fetch_source_metadata'),
```

### Frontend Component

**New React Component**: `SourceMetadataModal.js`

**Location**: `frontend/src/components/SourceMetadataModal.js`

**Component Structure**:
```jsx
import React, { useState } from 'react';
import APInterface from '../APInterface';

const SourceMetadataModal = ({ isOpen, onClose, onConfirm }) => {
  const [url, setUrl] = useState('');
  const [metadata, setMetadata] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [userEdits, setUserEdits] = useState({
    title: '',
    description: '',
    quote: ''  // User-added excerpt
  });

  const fetchMetadata = async () => {
    if (!url) return;

    setLoading(true);
    setError(null);

    try {
      const response = await APInterface.post('/api/sources/fetch-metadata/', { url });

      if (response.error) {
        setError(response.error.message);
        setMetadata(null);
      } else {
        setMetadata(response.data);
        // Pre-populate editable fields
        setUserEdits({
          title: response.data.title || '',
          description: response.data.description || '',
          quote: ''
        });
      }
    } catch (err) {
      setError('Failed to fetch metadata');
      setMetadata(null);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = () => {
    // Merge metadata with user edits
    const sourceData = {
      url: metadata.canonical_url || url,
      title: userEdits.title,
      description: userEdits.description,
      image_url: metadata.image_url,
      site_name: metadata.site_name,
      quote: userEdits.quote
    };

    onConfirm(sourceData);
    handleClose();
  };

  const handleClose = () => {
    setUrl('');
    setMetadata(null);
    setUserEdits({ title: '', description: '', quote: '' });
    setError(null);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content source-metadata-modal">
        <h2>Add Source from URL</h2>

        {/* URL Input Section */}
        <div className="url-input-section">
          <input
            type="url"
            placeholder="Enter URL (e.g., https://example.com/article)"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onBlur={fetchMetadata}
            className="url-input"
          />
          <button
            onClick={fetchMetadata}
            disabled={!url || loading}
            className="fetch-button"
          >
            {loading ? 'Fetching...' : 'Fetch Metadata'}
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="error-message">
            <p>{error}</p>
            <p className="hint">You can still manually enter information below.</p>
          </div>
        )}

        {/* Loading State */}
        {loading && <div className="loading-spinner">Loading preview...</div>}

        {/* Preview Section */}
        {metadata && (
          <div className="metadata-preview">
            <h3>Preview</h3>

            {/* Preview Card (read-only display) */}
            <div className="preview-card">
              {metadata.image_url && (
                <img
                  src={metadata.image_url}
                  alt="Preview"
                  className="preview-image"
                  onError={(e) => e.target.style.display = 'none'}
                />
              )}
              <div className="preview-text">
                <h4>{userEdits.title || 'No title'}</h4>
                <p className="preview-description">
                  {userEdits.description || 'No description available'}
                </p>
                <span className="preview-domain">
                  {metadata.site_name || new URL(url).hostname}
                </span>
              </div>
            </div>

            {/* Editable Fields */}
            <div className="editable-fields">
              <label>
                Title
                <input
                  type="text"
                  value={userEdits.title}
                  onChange={(e) => setUserEdits({...userEdits, title: e.target.value})}
                  placeholder="Source title"
                />
              </label>

              <label>
                Description
                <textarea
                  value={userEdits.description}
                  onChange={(e) => setUserEdits({...userEdits, description: e.target.value})}
                  placeholder="Brief description"
                  rows="3"
                />
              </label>

              <label>
                Quote/Excerpt (optional)
                <textarea
                  value={userEdits.quote}
                  onChange={(e) => setUserEdits({...userEdits, quote: e.target.value})}
                  placeholder="Add a relevant quote from this source (keep it brief)"
                  rows="4"
                />
                <span className="field-hint">
                  {userEdits.quote.length} characters (recommend &lt; 500 for fair use)
                </span>
              </label>
            </div>
          </div>
        )}

        {/* Manual Entry Fallback (if fetch failed or no metadata) */}
        {!metadata && !loading && url && (
          <div className="manual-entry">
            <p className="hint">Enter source information manually:</p>
            <label>
              Title
              <input
                type="text"
                value={userEdits.title}
                onChange={(e) => setUserEdits({...userEdits, title: e.target.value})}
                placeholder="Source title"
              />
            </label>
            <label>
              Description
              <textarea
                value={userEdits.description}
                onChange={(e) => setUserEdits({...userEdits, description: e.target.value})}
                placeholder="Brief description"
                rows="3"
              />
            </label>
          </div>
        )}

        {/* Action Buttons */}
        <div className="modal-actions">
          <button onClick={handleClose} className="cancel-button">
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={!url || !userEdits.title}
            className="confirm-button"
          >
            Create Source
          </button>
        </div>
      </div>
    </div>
  );
};

export default SourceMetadataModal;
```

**Styling** (add to existing CSS or create `SourceMetadataModal.css`):
```css
.source-metadata-modal {
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
}

.url-input-section {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.url-input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 14px;
}

.fetch-button {
  padding: 10px 20px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.fetch-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.preview-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 20px;
  background-color: #f9f9f9;
}

.preview-image {
  width: 100%;
  max-height: 300px;
  object-fit: cover;
}

.preview-text {
  padding: 15px;
}

.preview-text h4 {
  margin: 0 0 10px 0;
  font-size: 18px;
  color: #333;
}

.preview-description {
  margin: 0 0 10px 0;
  color: #666;
  font-size: 14px;
  line-height: 1.4;
}

.preview-domain {
  font-size: 12px;
  color: #999;
  text-transform: uppercase;
}

.editable-fields {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.editable-fields label {
  display: flex;
  flex-direction: column;
  font-weight: 500;
  font-size: 14px;
}

.editable-fields input,
.editable-fields textarea {
  margin-top: 5px;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 14px;
}

.field-hint {
  font-size: 12px;
  color: #666;
  margin-top: 5px;
}

.error-message {
  padding: 10px;
  background-color: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 4px;
  margin-bottom: 15px;
}

.error-message .hint {
  font-size: 12px;
  color: #666;
  margin-top: 5px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
}

.cancel-button,
.confirm-button {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.cancel-button {
  background-color: #f0f0f0;
  color: #333;
}

.confirm-button {
  background-color: #28a745;
  color: white;
}

.confirm-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}
```

**Integration Example** (where modal is triggered):
```jsx
// In your main component (e.g., GraphView or SourceManagement)
import SourceMetadataModal from './components/SourceMetadataModal';

function GraphView() {
  const [showSourceModal, setShowSourceModal] = useState(false);

  const handleSourceCreated = async (sourceData) => {
    // Create Source node via your existing API
    try {
      const response = await APInterface.post('/api/sources/', sourceData);
      // Handle success (add to graph, etc.)
      console.log('Source created:', response.data);
    } catch (error) {
      console.error('Failed to create source:', error);
    }
  };

  return (
    <div>
      <button onClick={() => setShowSourceModal(true)}>
        Add Source from URL
      </button>

      <SourceMetadataModal
        isOpen={showSourceModal}
        onClose={() => setShowSourceModal(false)}
        onConfirm={handleSourceCreated}
      />

      {/* Rest of your graph view */}
    </div>
  );
}
```

## Data Model Updates

**Source Node Schema** (if not already present):
```python
# In your Django model or AGE schema
{
  "url": "string (canonical URL)",
  "title": "string (from metadata or user)",
  "description": "string (brief summary)",
  "image_url": "string (thumbnail URL, nullable)",
  "site_name": "string (domain/site name)",
  "quote": "string (user-added excerpt, nullable)",
  "created_at": "timestamp",
  "created_by": "user_id"
}
```

## Implementation Phases

**Phase 1: Basic Metadata Fetch**
- Backend endpoint that fetches og: tags
- Simple fallbacks (title, description)
- Returns JSON response

**Phase 2: Frontend Modal**
- URL input and fetch trigger
- Display preview card
- Editable fields (title, description)
- Create Source action

**Phase 3: Enhancements**
- Quote/excerpt field with character counter
- Text fragment generation (for linking to quote location)
- Image caching/proxying (optional)
- Retry logic for failed fetches
- Support for academic sources (DOI resolution, arXiv, etc.)

**Phase 4: Polish**
- Loading states and animations
- Better error messages with suggestions
- Duplicate detection (warn if URL already exists)
- Bulk import (multiple URLs at once)

## Security Considerations

1. **SSRF Prevention**: Validate URLs, block internal/localhost addresses
2. **Timeout Handling**: Prevent hanging on slow/unresponsive sites
3. **Rate Limiting**: Prevent abuse of metadata fetch endpoint
4. **Content Validation**: Sanitize fetched HTML to prevent XSS
5. **User-Agent**: Identify as PublicSphere to comply with robots.txt expectations

## Testing Strategy

**Backend Tests**:
- Test with various URLs (Wikipedia, news sites, blogs)
- Test fallback behavior (missing og: tags)
- Test error cases (404, timeout, invalid URL)
- Test with og:image relative vs absolute URLs

**Frontend Tests**:
- Test modal open/close
- Test fetch success and error states
- Test edit functionality
- Test form validation

## Future Enhancements

- **Auto-suggest quotes**: Use LLM to extract key passages from fetched page
- **Citation formatting**: Generate proper citations (APA, MLA) from metadata
- **Archive.org integration**: Save permanent snapshots of sources
- **PDF support**: Extract metadata from PDF URLs
- **Academic database integration**: Fetch from CrossRef, PubMed APIs for papers
- **Browser extension**: One-click "Add to PublicSphere" from any webpage

## Open Questions

1. **Image storage**: Should we cache/proxy og:images or always link to original?
   - **Recommendation**: Link to original for v1, add caching later if needed

2. **Duplicate handling**: What if user adds same URL twice?
   - **Recommendation**: Check for existing Source with same URL, offer to reuse or create new

3. **Update strategy**: Should we re-fetch metadata periodically for stale sources?
   - **Recommendation**: Manual refresh only for v1

4. **Quote extraction**: Manual entry or automated?
   - **Recommendation**: Manual for v1, LLM-assisted later
