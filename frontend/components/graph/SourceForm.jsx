import { useState } from 'react';
import { CitationFetcher } from './CitationFetcher.jsx';
import { AuthorsInput } from './AuthorsInput.jsx';

/**
 * Complex form for creating/editing sources with full bibliographic metadata
 *
 * Fields are highlighted based on source_type to guide users toward expected fields
 *
 * @param {Object} props
 * @param {string} props.title - Source title (required)
 * @param {string} props.url - Source URL (optional)
 * @param {string} props.content - Source description
 * @param {string} props.source_type - Source type (journal_article, book, website, etc.)
 * @param {Array} props.authors - Authors array [{name, role, affiliation?}]
 * @param {string} props.doi - Digital Object Identifier
 * @param {string} props.publication_date - ISO 8601 date (YYYY-MM-DD or partial)
 * @param {string} props.container_title - Journal/book/website name
 * @param {string} props.publisher - Publisher name
 * @param {string} props.volume - Volume number
 * @param {string} props.issue - Issue number
 * @param {string} props.pages - Page range (e.g., "123-145")
 * @param {string} props.edition - Edition (books)
 * @param {string} props.isbn - ISBN (books)
 * @param {string} props.issn - ISSN (journals)
 * @param {string} props.arxiv_id - arXiv ID (preprints)
 * @param {Function} props.onTitleChange - (value: string) => void
 * @param {Function} props.onUrlChange - (value: string) => void
 * @param {Function} props.onContentChange - (value: string) => void
 * @param {Function} props.onSourceTypeChange - (value: string) => void
 * @param {Function} props.onAuthorsChange - (authors: Array) => void
 * @param {Function} props.onDoiChange - (value: string) => void
 * @param {Function} props.onPublicationDateChange - (value: string) => void
 * @param {Function} props.onContainerTitleChange - (value: string) => void
 * @param {Function} props.onPublisherChange - (value: string) => void
 * @param {Function} props.onVolumeChange - (value: string) => void
 * @param {Function} props.onIssueChange - (value: string) => void
 * @param {Function} props.onPagesChange - (value: string) => void
 * @param {Function} props.onEditionChange - (value: string) => void
 * @param {Function} props.onIsbnChange - (value: string) => void
 * @param {Function} props.onIssnChange - (value: string) => void
 * @param {Function} props.onArxivIdChange - (value: string) => void
 * @param {Function} props.onMetadataFetched - (metadata: Object) => void
 * @param {React.ReactNode} props.error - Error message or JSX
 */
export function SourceForm({
  title,
  url,
  content,
  source_type = '',
  authors = [],
  doi = '',
  publication_date = '',
  container_title = '',
  publisher = '',
  volume = '',
  issue = '',
  pages = '',
  edition = '',
  isbn = '',
  issn = '',
  arxiv_id = '',
  onTitleChange,
  onUrlChange,
  onContentChange,
  onSourceTypeChange,
  onAuthorsChange,
  onDoiChange,
  onPublicationDateChange,
  onContainerTitleChange,
  onPublisherChange,
  onVolumeChange,
  onIssueChange,
  onPagesChange,
  onEditionChange,
  onIsbnChange,
  onIssnChange,
  onArxivIdChange,
  onMetadataFetched,
  error
}) {
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Determine which fields should be highlighted for the selected source_type
  const highlightedFields = {
    journal_article: ['container_title', 'doi', 'volume', 'issue', 'pages', 'issn', 'publication_date'],
    preprint: ['container_title', 'doi', 'arxiv_id', 'publication_date'],
    book: ['publisher', 'isbn', 'edition', 'publication_date'],
    book_chapter: ['container_title', 'publisher', 'isbn', 'pages', 'publication_date'],
    website: ['container_title', 'publication_date'],
    newspaper: ['container_title', 'publication_date'],
    magazine: ['container_title', 'volume', 'issue', 'publication_date'],
    conference_paper: ['container_title', 'doi', 'pages', 'publication_date'],
    thesis: ['publisher', 'publication_date'],
    technical_report: ['publisher', 'publication_date'],
    government_document: ['publisher', 'publication_date']
  }[source_type] || [];

  const isHighlighted = (fieldName) => highlightedFields.includes(fieldName);

  const getFieldStyle = (fieldName) => ({
    border: isHighlighted(fieldName) ? '2px solid var(--accent-green)' : undefined,
    backgroundColor: isHighlighted(fieldName) ? 'rgba(104, 211, 145, 0.05)' : undefined
  });

  return (
    <>
      {/* Source Type - Required */}
      <div className="node-creation-field">
        <label className="node-creation-label">
          Source Type <span style={{ color: '#ff4444' }}>*</span>
        </label>
        <select
          className="node-creation-input"
          value={source_type}
          onChange={(e) => onSourceTypeChange(e.target.value)}
          required
          style={{ cursor: 'pointer' }}
        >
          <option value="">Select type...</option>
          <option value="journal_article">Journal Article</option>
          <option value="preprint">Preprint</option>
          <option value="book">Book</option>
          <option value="book_chapter">Book Chapter</option>
          <option value="conference_paper">Conference Paper</option>
          <option value="thesis">Thesis/Dissertation</option>
          <option value="technical_report">Technical Report</option>
          <option value="government_document">Government Document</option>
          <option value="website">Website</option>
          <option value="newspaper">Newspaper Article</option>
          <option value="magazine">Magazine Article</option>
          <option value="dataset">Dataset</option>
          <option value="media">Media (Video/Audio)</option>
          <option value="legal">Legal Document</option>
          <option value="testimony">Testimony</option>
        </select>
      </div>

      {/* Title - Required */}
      <div className="node-creation-field">
        <label className="node-creation-label">
          Title <span style={{ color: '#ff4444' }}>*</span>
        </label>
        <input
          type="text"
          className={`node-creation-input ${!title.trim() ? 'error' : ''}`}
          placeholder="Source title (required)"
          value={title}
          onChange={(e) => onTitleChange(e.target.value)}
          required
        />
      </div>

      {/* URL with Citation Fetcher */}
      <div className="node-creation-field">
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '4px'
        }}>
          <label className="node-creation-label" style={{ margin: 0 }}>URL</label>
          {url && url.trim() && (
            <CitationFetcher url={url} onMetadataFetched={onMetadataFetched} />
          )}
        </div>
        <input
          type="url"
          className="node-creation-input"
          placeholder="https://..."
          value={url}
          onChange={(e) => onUrlChange(e.target.value)}
        />
      </div>

      {/* Authors */}
      <AuthorsInput authors={authors} onChange={onAuthorsChange} />

      {/* Common Bibliographic Fields */}
      <div className="node-creation-field">
        <label className="node-creation-label">
          DOI {isHighlighted('doi') && <span style={{ color: 'var(--accent-green)', fontSize: '0.75rem' }}>(suggested)</span>}
        </label>
        <input
          type="text"
          className="node-creation-input"
          placeholder="10.1234/example"
          value={doi}
          onChange={(e) => onDoiChange(e.target.value)}
          style={getFieldStyle('doi')}
        />
      </div>

      <div className="node-creation-field">
        <label className="node-creation-label">
          Publication Date {isHighlighted('publication_date') && <span style={{ color: 'var(--accent-green)', fontSize: '0.75rem' }}>(suggested)</span>}
        </label>
        <input
          type="text"
          className="node-creation-input"
          placeholder="YYYY-MM-DD or YYYY"
          value={publication_date}
          onChange={(e) => onPublicationDateChange(e.target.value)}
          style={getFieldStyle('publication_date')}
        />
      </div>

      <div className="node-creation-field">
        <label className="node-creation-label">
          Container Title {isHighlighted('container_title') && <span style={{ color: 'var(--accent-green)', fontSize: '0.75rem' }}>(suggested)</span>}
        </label>
        <input
          type="text"
          className="node-creation-input"
          placeholder="Journal name, book title, or website name"
          value={container_title}
          onChange={(e) => onContainerTitleChange(e.target.value)}
          style={getFieldStyle('container_title')}
        />
        <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
          Journal name, book title (for chapters), website name, etc.
        </div>
      </div>

      {/* Advanced Fields Toggle */}
      <button
        type="button"
        onClick={() => setShowAdvanced(!showAdvanced)}
        style={{
          width: '100%',
          padding: '8px',
          fontSize: '0.85rem',
          backgroundColor: 'transparent',
          color: 'var(--accent-blue)',
          border: '1px solid var(--attr-border)',
          borderRadius: '4px',
          cursor: 'pointer',
          marginTop: '8px'
        }}
      >
        {showAdvanced ? '▼ Hide' : '▶ Show'} Advanced Fields (publisher, volume, identifiers, etc.)
      </button>

      {/* Advanced Fields */}
      {showAdvanced && (
        <>
          <div className="node-creation-field">
            <label className="node-creation-label">
              Publisher {isHighlighted('publisher') && <span style={{ color: 'var(--accent-green)', fontSize: '0.75rem' }}>(suggested)</span>}
            </label>
            <input
              type="text"
              className="node-creation-input"
              placeholder="Publisher name"
              value={publisher}
              onChange={(e) => onPublisherChange(e.target.value)}
              style={getFieldStyle('publisher')}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
            <div className="node-creation-field" style={{ margin: 0 }}>
              <label className="node-creation-label">
                Volume {isHighlighted('volume') && <span style={{ color: 'var(--accent-green)', fontSize: '0.75rem' }}>✓</span>}
              </label>
              <input
                type="text"
                className="node-creation-input"
                placeholder="Vol."
                value={volume}
                onChange={(e) => onVolumeChange(e.target.value)}
                style={getFieldStyle('volume')}
              />
            </div>
            <div className="node-creation-field" style={{ margin: 0 }}>
              <label className="node-creation-label">
                Issue {isHighlighted('issue') && <span style={{ color: 'var(--accent-green)', fontSize: '0.75rem' }}>✓</span>}
              </label>
              <input
                type="text"
                className="node-creation-input"
                placeholder="Iss."
                value={issue}
                onChange={(e) => onIssueChange(e.target.value)}
                style={getFieldStyle('issue')}
              />
            </div>
            <div className="node-creation-field" style={{ margin: 0 }}>
              <label className="node-creation-label">
                Pages {isHighlighted('pages') && <span style={{ color: 'var(--accent-green)', fontSize: '0.75rem' }}>✓</span>}
              </label>
              <input
                type="text"
                className="node-creation-input"
                placeholder="123-145"
                value={pages}
                onChange={(e) => onPagesChange(e.target.value)}
                style={getFieldStyle('pages')}
              />
            </div>
          </div>

          <div className="node-creation-field">
            <label className="node-creation-label">
              Edition {isHighlighted('edition') && <span style={{ color: 'var(--accent-green)', fontSize: '0.75rem' }}>(suggested)</span>}
            </label>
            <input
              type="text"
              className="node-creation-input"
              placeholder="e.g., 2nd edition"
              value={edition}
              onChange={(e) => onEditionChange(e.target.value)}
              style={getFieldStyle('edition')}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
            <div className="node-creation-field" style={{ margin: 0 }}>
              <label className="node-creation-label">
                ISBN {isHighlighted('isbn') && <span style={{ color: 'var(--accent-green)', fontSize: '0.75rem' }}>✓</span>}
              </label>
              <input
                type="text"
                className="node-creation-input"
                placeholder="ISBN"
                value={isbn}
                onChange={(e) => onIsbnChange(e.target.value)}
                style={getFieldStyle('isbn')}
              />
            </div>
            <div className="node-creation-field" style={{ margin: 0 }}>
              <label className="node-creation-label">
                ISSN {isHighlighted('issn') && <span style={{ color: 'var(--accent-green)', fontSize: '0.75rem' }}>✓</span>}
              </label>
              <input
                type="text"
                className="node-creation-input"
                placeholder="ISSN"
                value={issn}
                onChange={(e) => onIssnChange(e.target.value)}
                style={getFieldStyle('issn')}
              />
            </div>
            <div className="node-creation-field" style={{ margin: 0 }}>
              <label className="node-creation-label">
                arXiv ID {isHighlighted('arxiv_id') && <span style={{ color: 'var(--accent-green)', fontSize: '0.75rem' }}>✓</span>}
              </label>
              <input
                type="text"
                className="node-creation-input"
                placeholder="2301.12345"
                value={arxiv_id}
                onChange={(e) => onArxivIdChange(e.target.value)}
                style={getFieldStyle('arxiv_id')}
              />
            </div>
          </div>
        </>
      )}

      {/* Description/Content */}
      <div className="node-creation-field">
        <label className="node-creation-label">Description</label>
        <textarea
          className="node-creation-textarea"
          placeholder="Describe the evidence..."
          value={content}
          onChange={(e) => onContentChange(e.target.value)}
        />
      </div>

      {error && (
        <div className="node-creation-error">
          {error}
        </div>
      )}
    </>
  );
}
