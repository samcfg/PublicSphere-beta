# Prompt 1
We are working on refining the backend changes that were made between the current local codebase and the git repo. Find them. It 
should be 3 categories: "suggested edits" system, SourceNode, and the URL parsing function. 
We will zoom in on the sourceNode and URL parsing function as part of the system by which users create sourceNodes, and the content 
that needs to be stored within. Understand these changes practically as background for the following design discussion. 

### Completed Task: 
To make this design good, we will do a critical comparitive analysis of current systems of citation and their citation types. I am 
functionally familiar with written standards like MLA and APA, what are other kinds of standards? 
I found that there is no standard for this, and internet-based citation is often more pragmatic, less standardized. So it makes sense that we make our own, and map its information to the types of information recorded in standard systems. This will allow automatic citation extraction. 
## Design requirement 1:
**source_type** - The category of source within a citation system which dictates which fields are necessary.
We need this for two reasons: 
1. Reader clarity: Users will encounter sources in the cytoscape graph, and must be able to quickly read the type of information 
that a source is. For example, a journal article or an anecdote. This should not be merely implicit by other formatting or 
affiliation, for that is unnecessary mental strain for user. 
2. Source Node Creation Flow: Source nodes will be created more easily if there is an option to select which type they are using, 
and then visually hilight or show the fields that are relevant to be filled in by that type. 
 
 - Dublin Core's fields almost seem to be discressional, this aligns well with the site's pragmatism
 - Consider having a text "genre" field that selects subtypes of things, e.g. PHD thesis

# On RichLinkView
- need to add **thumbnail_link** field on all sources (optional), and get that out of the meta (og:image)

# On Source Node Creation & AutoParse

## Frontend HI (Assuming URL Parse first)

  Loading state:
  ┌─────────────────────────────────────┐
  │ Create Source Node                  │
  ├─────────────────────────────────────┤
  │ URL: https://www.nytimes.com/...   │
  │   (Type)                                  │
  │   (Other fields)                                  │
  │ ⟳ Fetching metadata...              │
  └─────────────────────────────────────┘

  After fetch (high confidence):
  ┌─────────────────────────────────────┐
  │ Create Source Node                  │
  ├─────────────────────────────────────┤
  │ ✓ Detected: Newspaper (High confidence)
  │                                     │
  │ Source Type: [Newspaper ▼]         │
  │ Title: Scientists Discover...      │
  │ Authors: Jane Reporter             │
  │ Publication: The New York Times    │
  │ Date: 2024-03-15                   │
  │ URL: https://...                   │
  │ Accessed: 2025-01-30               │
  │                                     │
  │ Advanced fields ▼                  │
  │   Section: Science                 │
  │                                     │
  │ [Create Source Node]               │
  └─────────────────────────────────────┘

  After fetch (low confidence):
  ┌─────────────────────────────────────┐
  │ Create Source Node                  │
  ├─────────────────────────────────────┤
  │ ⚠ Detected: Website (Low confidence)
  │ Please review and complete fields  │
  │                                     │
  │ Source Type: [Website ▼]           │
  │   Try: Legal | Media | Report       │
  │                                     │
  │ Title: [empty - needs entry]       │
  │ URL: https://...                   │
  │ Accessed: 2025-01-30               │
  │                                     │
  │ [Create Source Node]               │
  └─────────────────────────────────────┘


Type Detection: 
> 1. API responses (high confidence):
  - CrossRef: Returns type field → maps to journal_article, book, conference_paper
  - arXiv: Always → preprint

  2. schema.org JSON-LD (medium confidence):
  - NewsArticle → newspaper
  - ScholarlyArticle → journal_article
  - Book → book
  
  2. whitelist -> common media players/hosts
  - Podcast apps? 

  3. Fallback (low confidence):
  - Everything else → website

Things which Requires Manual Input
  - Anecdotal
  - Legal (Requires Moderator Approval?)
  - Technical Report
  - Media
Say something on detection of "magazine" 

# Source Formats
## Types
- academic journal article
- preprint
- book (contains option for chapter)
- book chapter
- website
- newspaper
- thesis
- conference paper (niche, probably wont be supported by manual UI, but something that the auto-parser may catch)
- magazine
- Government/policy document
- Dataset
- Social Media Post
- Oral history

- technical report (Non-peer-reviewed documents produced by institutions)
- anecdote
- legal (citing laws)
- media (includes photo, audio, video)

### Uniform Fields
label='Source',
'id': str,
'title': str,
'source_type': str,
optional: ={
'authors': str, # JSON string: {"name": "...", "role": "author"}]
'thumbnail_link': str,  # Optional for ALL types - og:image, cover art, featured images, etc.
'url': str,
}
### Type-Based Fields
**Publicaton**
'publication_date': str,
'container_title': str, # Journal/book/website/conference name
'publisher': str,
'publisher_location': str,
**Volume/Issue/Pages**
'volume': str,
'issue': str,
'pages': str,
**Book**
'edition'
chapter_title / chapter_number
**Identifiers** (entry fields available if type not chosen)
'doi': str,
'isbn': str,
'issn': str,
'pmid': str,  # PubMed ID (biomedical articles)
'pmcid': str,  # PubMed Central ID (open-access full text)
'arxiv_id': str,  # arXiv identifier (preprints)
'handle': str,  # Handle System identifier (institutional repositories)
**Conference_paper**
conference
conference date 
**Technical Report**
'institution'
'report_number'

**media**
'media format'

'Editors': str

'accessed_date': str,
'excerpt': str
'content': str

### Legal schema (novel fields also in optional, or 4 tier json)
  {
      "node_id": "uuid-...",
      "title": "Miranda v. Arizona",  # REQUIRED (Tier 2)
      "source_type": "legal",  # REQUIRED

      # Core legal fields (Tier 2 + Tier 3)
      "jurisdiction": "United States",  # REQUIRED (Tier 2)
      "legal_category": "case",  # REQUIRED (Tier 2)

      # Tier 1: Canonical identifiers
      "url":
  "https://www.courtlistener.com/opinion/107252/miranda-v-arizona/",
      "persistent_id": null,  # e.g., ECLI, ELI, DOI
      "persistent_id_type": null,  # Auto-detected or null

      # Tier 3: Common citation fields (flatten into top-level for 
  queryability)
      "court": "Supreme Court of the United States",
      "decision_date": "1966-06-13",
      "case_name": "Miranda v. Arizona",  # May duplicate title
      "code": null,  # For statutes
      "section": null,  # For statutes
      "publication_date": null,  # For statutes

      # Standard fields
      "accessed_date": "2025-02-02",
      "excerpt": "...",
      "content": "...",

      # Tier 4: Everything else goes in metadata JSON
      "metadata": {
          "reporter": "U.S.",
          "reporter_volume": "384",
          "first_page": "436",
          "file_number": null,
          "original_language_title": null,
          "original_script": null,
          "issuing_authority": null,
          "promulgation_date": null,
          "transliteration_system": null,
          "author_death_date": null,
          "citation_notes": "Seminal case establishing Miranda rights"
      }
  }



      # Standard fields
      "accessed_date": "2025-02-02",
      "excerpt": "...",
  }

---

# Complete Source Type Specifications

## 1. journal_article
**Purpose**: Peer-reviewed academic articles in scholarly journals

**Required Fields**:
- `title`: Article title
- `authors`: JSON array of author objects
- `container_title`: Journal name
- `publication_date`: Publication date

**Typical Optional Fields**:
- `volume`: Journal volume number
- `issue`: Issue number
- `pages`: Page range (e.g., "123-145")
- `doi`: Digital Object Identifier
- `issn`: International Standard Serial Number
- `pmid`: PubMed ID (for biomedical literature)
- `pmcid`: PubMed Central ID (for open-access versions)
- `url`: Link to article
- `accessed_date`: When the article was accessed online

**Storage**: All fields top-level in SourceVersion model

---

## 2. preprint
**Purpose**: Pre-publication scholarly articles (arXiv, bioRxiv, etc.)

**Required Fields**:
- `title`: Preprint title
- `authors`: JSON array of author objects
- `publication_date`: Upload/posting date

**Typical Optional Fields**:
- `container_title`: Preprint server name (e.g., "arXiv")
- `doi`: Digital Object Identifier
- `arxiv_id`: arXiv identifier (e.g., "2401.12345")
- `url`: Link to preprint
- `accessed_date`: Access date
- `metadata`: {"version": "v2"}

**Storage**: All fields top-level except version info in metadata JSON

---

## 3. book
**Purpose**: Books and book chapters (both handled by this type)

**Required Fields**:
- `title`: Book title OR chapter title (if citing specific chapter)
- `authors`: Authors (of book or chapter)

**Typical Optional Fields**:
- `container_title`: Book title (if citing chapter within edited volume)
- `editors`: JSON array of editor objects (for edited volumes)
- `publisher`: Publishing house
- `publication_date`: Publication year/date
- `edition`: Edition number (e.g., "3rd")
- `isbn`: International Standard Book Number
- `pages`: Page range (if citing chapter)
- `url`: Link to online version
- `metadata`: {"chapter_number": "5", "chapter_title": "..."} (if needed separately)

**Storage**: All fields top-level; use `container_title` when `title` is chapter

---

## 4. website
**Purpose**: General web content not fitting other categories

**Required Fields**:
- `title`: Page title
- `url`: Page URL

**Typical Optional Fields**:
- `authors`: JSON array (if byline exists)
- `container_title`: Website name
- `publication_date`: Publication/update date
- `accessed_date`: When accessed
- `thumbnail_link`: og:image URL

**Storage**: All fields top-level

---

## 5. newspaper
**Purpose**: News articles from newspapers (print or digital)

**Required Fields**:
- `title`: Article headline
- `container_title`: Newspaper name (e.g., "The New York Times")
- `publication_date`: Publication date

**Typical Optional Fields**:
- `authors`: JSON array of reporters
- `url`: Link to article
- `accessed_date`: Access date
- `pages`: Print page numbers (if applicable)
- `metadata`: {"section": "Science", "edition": "Late Edition"}

**Storage**: All fields top-level except section/edition in metadata

---

## 6. magazine
**Purpose**: Magazine articles (periodicals, not newspapers)

**Required Fields**:
- `title`: Article title
- `container_title`: Magazine name
- `publication_date`: Publication date

**Typical Optional Fields**:
- `authors`: JSON array
- `volume`: Volume number
- `issue`: Issue number
- `pages`: Page range
- `url`: Link to article
- `accessed_date`: Access date

**Storage**: All fields top-level

---

## 7. thesis
**Purpose**: Dissertations and theses

**Required Fields**:
- `title`: Thesis title
- `authors`: JSON array (usually single author)
- `publication_date`: Year completed

**Typical Optional Fields**:
- `publisher`: University name (institution granting degree)
- `url`: Link to institutional repository or ProQuest
- `doi`: Digital Object Identifier
- `handle`: Handle identifier (institutional repositories)
- `metadata`: {"degree_type": "PhD", "department": "Physics", "advisor": "..."}

**Storage**: All fields top-level except degree details in metadata

---

## 8. conference_paper
**Purpose**: Papers presented at academic/professional conferences

**Required Fields**:
- `title`: Paper title
- `authors`: JSON array
- `container_title`: Proceedings title
- `publication_date`: Publication date

**Typical Optional Fields**:
- `publisher`: Publisher of proceedings
- `pages`: Page range
- `doi`: Digital Object Identifier
- `url`: Link to paper
- `metadata`: {"event_name": "ICML 2024", "event_date": "2024-07-21"}

**Storage**: All fields top-level except event details in metadata

---

## 9. technical_report
**Purpose**: Institutional research reports (non-peer-reviewed)

**Required Fields**:
- `title`: Report title
- `publisher`: Issuing institution (e.g., "RAND Corporation")
- `publication_date`: Publication date

**Typical Optional Fields**:
- `authors`: JSON array
- `url`: Link to report
- `doi`: Digital Object Identifier
- `metadata`: {"report_number": "NASA-TM-2024-104567", "institution": "NASA"}

**Storage**: All fields top-level except report_number in metadata (or top-level if frequently queried)

---

## 10. government_document
**Purpose**: Government publications, white papers, policy documents

**Required Fields**:
- `title`: Document title
- `publisher`: Issuing government agency
- `publication_date`: Publication date

**Typical Optional Fields**:
- `authors`: JSON array (if attributed)
- `url`: Link to document
- `metadata`: {"document_number": "GAO-24-106380", "government_level": "federal"}

**Storage**: All fields top-level except document_number/level in metadata

---

## 11. dataset
**Purpose**: Research datasets, data repositories

**Required Fields**:
- `title`: Dataset title
- `url`: Repository URL or DOI resolver

**Typical Optional Fields**:
- `authors`: JSON array of dataset creators
- `publisher`: Repository name (e.g., "Zenodo", "Figshare")
- `publication_date`: Publication/upload date
- `doi`: Digital Object Identifier (highly recommended)
- `persistent_id`: DOI or other persistent identifier
- `persistent_id_type`: "DOI"
- `accessed_date`: Access date
- `metadata`: {"version": "1.2", "license": "CC-BY-4.0"}

**Storage**: All fields top-level; version/license in metadata

---

## 12. media
**Purpose**: Video, audio, images (YouTube, podcasts, photos)

**Required Fields**:
- `title`: Media title
- `url`: Link to media

**Typical Optional Fields**:
- `authors`: JSON array (creators/performers)
- `publication_date`: Upload/publication date
- `container_title`: Series/album/channel name
- `thumbnail_link`: Thumbnail image URL
- `accessed_date`: Access date
- `metadata`: {"media_format": "video", "duration": "PT1H30M", "platform": "YouTube"}

**Storage**: All fields top-level except duration/platform in metadata

---

## 13. legal
**Purpose**: Case law, statutes, regulations, treaties

**Required Fields**:
- `title`: Case name or statute name
- `jurisdiction`: Legal jurisdiction (e.g., "United States", "Germany")
- `legal_category`: Type ("case", "statute", "regulation", "treaty")

**Tier 1 (Canonical Identifiers)**:
- `url`: Stable URL to authoritative source
- `persistent_id`: ECLI, ELI, DOI, Public Law number
- `persistent_id_type`: Auto-detected type of identifier

**Tier 3 (Common Citation Fields)**:
- For cases: `court`, `decision_date`, `case_name`
- For statutes: `code`, `section`, `article`, `publication_date`

**Tier 4 (Traditional Citation Metadata)** - stored in `metadata` JSON:
- `reporter`, `reporter_volume`, `first_page`, `file_number`
- `original_language_title`, `original_script`
- `issuing_authority`, `promulgation_date`
- `transliteration_system`, `author_death_date` (for Islamic law)
- `citation_notes`

**Storage**: Tiers 1-3 top-level; Tier 4 in metadata JSON

---

## 14. personal_communication
**Purpose**: Anecdotes, personal observations, private communications, interviews

**Required Fields**:
- `title`: Descriptive title of the communication
- `authors`: JSON array (communicator/interviewee)

**Typical Optional Fields**:
- `publication_date`: Date of communication/observation
- `metadata`: {"communication_type": "interview", "interviewer": "...", "location": "..."}

**Storage**: All fields top-level except communication details in metadata

---

## Storage Performance Analysis


---

## Thumbnail Images

**Decision**: `thumbnail_link` is optional for ALL source types without exception.

**Rationale**:
- Most types have thumbnails via OpenGraph metadata (og:image), book covers, article featured images, video thumbnails
- Even types with rare thumbnails (legal documents, personal communications) benefit from field availability for edge cases
- Zero storage cost when NULL
- UI can conditionally display based on presence
- Prevents artificial limitations on user flexibility

**Auto-population**: URL parser should extract og:image, Twitter card images, or schema.org image fields for all types.

---

## Final Reflection on Schema Completeness

**Coverage Assessment**: The 14 source types cover the vast majority of citation needs for argument mapping:

✓ **Academic sources**: journal_article, preprint, book, thesis, conference_paper
✓ **Media sources**: newspaper, magazine, website, media (video/audio/image)
✓ **Institutional sources**: technical_report, government_document, dataset
✓ **Legal sources**: legal (cases, statutes, regulations, treaties)
✓ **Personal sources**: personal_communication (anecdotes, interviews, observations)

**Potential Gaps**:
1. **Standards/Specifications** (ISO, RFC, W3C specs) - Could use `technical_report` or add dedicated type
2. **Patents** - Currently no type; rare in argument mapping but could add if needed
3. **Archival Materials** (manuscripts, letters, historical documents) - Could use `personal_communication` or add `archival_document` type
4. **Religious Texts** (Bible, Quran, etc.) - Could use `book` but may need special citation fields (chapter:verse)

**Recommendation**: Current schema is sufficient for MVP. Monitor usage patterns to determine if specialized types (patents, archival, religious texts) warrant addition. The metadata JSON provides escape hatch for edge cases.

**Field Completeness**: All major citation systems (MLA, APA, Chicago, Bluebook, Vancouver) can be mapped to this field set. The combination of top-level fields + metadata JSON provides flexibility without schema bloat.
