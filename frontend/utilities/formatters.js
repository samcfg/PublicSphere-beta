/**
 * Transform DRF API graph response into Cytoscape.js format
 * Backend already parses AGE format - this transforms the clean JSON structure
 * @param {Object} graphData - {claims: [...], sources: [...], edges: [...]} from /api/graph/
 * @returns {Object} - {elements: [...]} formatted for Cytoscape
 */
export function formatForCytoscape(graphData) {
  const elements = [];

  // Process claims (nodes)
  if (graphData.claims) {
    graphData.claims.forEach((row) => {
      try {
        const claim = row.claim; // Already parsed by database.py
        elements.push({
          data: {
            id: claim.properties.id,
            label: claim.label || 'Claim',
            type: 'claim',
            ...claim.properties
          },
          classes: 'claim' // CSS class for styling
        });
      } catch (error) {
        console.error('Failed to process claim:', error.message, row);
      }
    });
  }

  // Process sources (nodes)
  if (graphData.sources) {
    graphData.sources.forEach((row) => {
      try {
        const source = row.source; // Already parsed by database.py
        elements.push({
          data: {
            id: source.properties.id,
            label: source.label || 'Source',
            type: 'source',
            ...source.properties
          },
          classes: 'source' // CSS class for styling
        });
      } catch (error) {
        console.error('Failed to process source:', error.message, row);
      }
    });
  }

  // Process edges (connections)
  if (graphData.edges) {
    graphData.edges.forEach((row) => {
      try {
        const connection = row.connection; // Already parsed by database.py

        // AGE edges have start_id (source) and end_id (target) - use these for correct direction
        // Compare AGE internal IDs to determine which node is source vs target
        const sourceNode = row.node.id === connection.start_id ? row.node : row.other;
        const targetNode = row.node.id === connection.end_id ? row.node : row.other;

        elements.push({
          data: {
            id: connection.properties.id,
            source: sourceNode.properties.id,  // Correct source based on start_id
            target: targetNode.properties.id,  // Correct target based on end_id
            label: connection.label || 'Connection',
            composite_id: connection.properties.composite_id,
            logic_type: connection.properties.logic_type,
            notes: connection.properties.notes,
            ...connection.properties
          },
          classes: connection.properties.logic_type || 'connection' // CSS class based on logic type
        });
      } catch (error) {
        console.error('Failed to process edge:', error.message, row);
      }
    });
  }

  return { elements };
}

// ============================================================================
// SOURCE METADATA FORMATTERS
// ============================================================================

/**
 * Format authors array to readable string
 * @param {Array} authors - [{name: "...", role: "author"}, ...]
 * @returns {string} - "Author1, Author2, Author3" or null
 */
export function formatAuthors(authors) {
  if (!authors || !Array.isArray(authors) || authors.length === 0) {
    return null;
  }

  return authors
    .filter(author => author.name)
    .map(author => author.name)
    .join(', ');
}

/**
 * Format editors array to readable string
 * @param {Array} editors - [{name: "...", role: "editor"}, ...]
 * @returns {string} - "Editor1, Editor2" or null
 */
export function formatEditors(editors) {
  if (!editors || !Array.isArray(editors) || editors.length === 0) {
    return null;
  }

  return editors
    .filter(editor => editor.name)
    .map(editor => editor.name)
    .join(', ');
}

/**
 * Format source type to human-readable label
 * @param {string} sourceType - 'journal_article', 'preprint', etc.
 * @returns {string} - "Journal Article", "Preprint", etc.
 */
export function formatSourceType(sourceType) {
  if (!sourceType) return 'Unknown';

  const typeLabels = {
    'journal_article': 'Journal Article',
    'preprint': 'Preprint',
    'book': 'Book',
    'website': 'Website',
    'newspaper': 'Newspaper',
    'magazine': 'Magazine',
    'thesis': 'Thesis',
    'conference_paper': 'Conference Paper',
    'technical_report': 'Technical Report',
    'government_document': 'Government Document',
    'dataset': 'Dataset',
    'media': 'Media',
    'legal': 'Legal Document',
    'testimony': 'Testimony'
  };

  return typeLabels[sourceType] || sourceType;
}

/**
 * Format legal category to human-readable label
 * @param {string} category - 'case', 'statute', etc.
 * @returns {string} - "Case", "Statute", etc.
 */
export function formatLegalCategory(category) {
  if (!category) return null;

  const categoryLabels = {
    'case': 'Case',
    'statute': 'Statute',
    'regulation': 'Regulation',
    'treaty': 'Treaty'
  };

  return categoryLabels[category] || category;
}

/**
 * Format publication date (handles partial dates)
 * @param {string} date - "2024", "2024-03", or "2024-03-15"
 * @returns {string} - Formatted date or original string
 */
export function formatPublicationDate(date) {
  if (!date) return null;

  // Handle partial dates (just year, or year-month)
  if (/^\d{4}$/.test(date)) {
    return date; // Just year
  }
  if (/^\d{4}-\d{2}$/.test(date)) {
    const [year, month] = date.split('-');
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return `${monthNames[parseInt(month) - 1]} ${year}`;
  }

  // Full date
  try {
    const dateObj = new Date(date);
    return dateObj.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
  } catch {
    return date; // Return original if parsing fails
  }
}

/**
 * Get structured source metadata for display
 * Returns array of {label, value} objects for non-empty fields
 * @param {Object} source - Source node data
 * @returns {Array} - [{label: "Authors", value: "..."}, ...]
 */
export function getSourceMetadataFields(source) {
  if (!source) return [];

  const fields = [];

  // Helper to add field if value exists
  const addField = (label, value) => {
    if (value !== null && value !== undefined && value !== '') {
      fields.push({ label, value });
    }
  };

  // Required fields
  addField('Title', source.title);
  addField('Type', formatSourceType(source.source_type));

  // Authors and Editors
  const authorsStr = formatAuthors(source.authors);
  const editorsStr = formatEditors(source.editors);
  addField('Authors', authorsStr);
  addField('Editors', editorsStr);

  // Publication metadata
  addField('Publication Date', formatPublicationDate(source.publication_date));
  addField('Container Title', source.container_title);
  addField('Publisher', source.publisher);
  addField('Publisher Location', source.publisher_location);

  // Volume/Issue/Pages
  addField('Volume', source.volume);
  addField('Issue', source.issue);
  addField('Pages', source.pages);
  addField('Edition', source.edition);

  // URL and Access
  addField('URL', source.url);
  addField('Accessed Date', source.accessed_date);

  // Identifiers
  addField('DOI', source.doi);
  addField('ISBN', source.isbn);
  addField('ISSN', source.issn);
  addField('PMID', source.pmid);
  addField('PMC ID', source.pmcid);
  addField('arXiv ID', source.arxiv_id);
  addField('Handle', source.handle);
  if (source.persistent_id) {
    const idType = source.persistent_id_type ? ` (${source.persistent_id_type})` : '';
    addField('Persistent ID', `${source.persistent_id}${idType}`);
  }

  // Legal-specific
  addField('Jurisdiction', source.jurisdiction);
  addField('Legal Category', formatLegalCategory(source.legal_category));
  addField('Court', source.court);
  addField('Decision Date', source.decision_date);
  addField('Case Name', source.case_name);
  addField('Code', source.code);
  addField('Section', source.section);

  // Content fields
  addField('Excerpt', source.excerpt);
  addField('Content', source.content);

  return fields;
}
