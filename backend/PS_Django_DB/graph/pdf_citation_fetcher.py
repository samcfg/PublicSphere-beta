"""
PDF citation metadata extraction (UNUSED - extracted from citation_fetcher.py).

This module provides PDF-specific citation extraction but is currently not integrated
into the main citation flow. The web UI only supports URL-based citation fetching.
"""

import re
from typing import Optional
from datetime import date

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


class PDFCitationFetcher:
    """Extract citation metadata from PDF files (UNUSED)"""

    @classmethod
    def fetch_from_pdf(cls, pdf_file, crossref_fetcher_fn=None) -> dict:
        """
        Extract metadata from uploaded PDF file.

        Args:
            pdf_file: Django UploadedFile object
            crossref_fetcher_fn: Optional function to fetch from CrossRef (DOI) -> dict

        Returns:
            {
                'success': bool,
                'source': str,
                'confidence': str,
                'metadata': dict
            }
        """
        if not PDF_AVAILABLE:
            return {
                'success': False,
                'source': 'pdf_unavailable',
                'confidence': 'low',
                'metadata': {'error': 'PDF extraction not available (PyPDF2 not installed)'}
            }

        # 1. Extract XMP metadata (embedded by publishers)
        metadata = cls._extract_pdf_xmp(pdf_file)
        if metadata.get('doi') and crossref_fetcher_fn:
            # If we found DOI in PDF, fetch from CrossRef
            crossref_data = crossref_fetcher_fn(metadata['doi'])
            if crossref_data:
                return {
                    'success': True,
                    'source': 'pdf_xmp_crossref',
                    'confidence': 'high',
                    'metadata': crossref_data
                }

        # 2. Pattern match for DOI in PDF text
        doi = cls._extract_doi_from_pdf_text(pdf_file)
        if doi and crossref_fetcher_fn:
            crossref_data = crossref_fetcher_fn(doi)
            if crossref_data:
                return {
                    'success': True,
                    'source': 'pdf_text_crossref',
                    'confidence': 'high',
                    'metadata': crossref_data
                }

        # 3. Return whatever we extracted from PDF metadata
        if metadata:
            return {
                'success': True,
                'source': 'pdf_metadata',
                'confidence': 'medium',
                'metadata': metadata
            }

        # Fallback: no metadata found
        return {
            'success': False,
            'source': 'pdf_fallback',
            'confidence': 'low',
            'metadata': {'source_type': 'unknown'}
        }

    @staticmethod
    def _extract_pdf_xmp(pdf_file) -> dict:
        """Extract XMP metadata embedded in PDF"""
        if not PDF_AVAILABLE:
            return {}

        try:
            # Reset file pointer to beginning
            pdf_file.seek(0)
            reader = PyPDF2.PdfReader(pdf_file)
            info = reader.metadata

            if not info:
                return {}

            # Parse PDF date format (D:20210115120000) to ISO 8601
            creation_date = info.get('/CreationDate', '')
            pub_date = None
            if creation_date and creation_date.startswith('D:'):
                date_str = creation_date[2:10]  # Extract YYYYMMDD
                if len(date_str) == 8:
                    pub_date = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"

            authors = []
            author_str = info.get('/Author')
            if author_str:
                authors.append({'name': author_str, 'role': 'author'})

            metadata = {
                'title': info.get('/Title'),
                'authors': authors if authors else None,
                'publication_date': pub_date,
                'source_type': 'unknown',
            }

            return {k: v for k, v in metadata.items() if v is not None}

        except Exception as e:
            print(f"PDF XMP extraction failed: {e}")
            return {}

    @staticmethod
    def _extract_doi_from_pdf_text(pdf_file) -> Optional[str]:
        """
        Extract DOI by pattern matching in PDF text.

        Checks first 2 pages and last page (common DOI locations).
        """
        if not PDF_AVAILABLE:
            return None

        try:
            # Reset file pointer
            pdf_file.seek(0)
            reader = PyPDF2.PdfReader(pdf_file)

            # Check first 2 pages and last page
            pages_to_check = [0, 1]
            if len(reader.pages) > 2:
                pages_to_check.append(len(reader.pages) - 1)

            for page_num in pages_to_check:
                if page_num < len(reader.pages):
                    text = reader.pages[page_num].extract_text()

                    # Pattern: doi: 10.1234/foo or DOI: 10.1234/foo
                    pattern = r'doi:?\s*(10\.\d{4,}/[^\s]+)'
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        return match.group(1).rstrip('.')

            return None

        except Exception as e:
            print(f"PDF DOI extraction failed: {e}")
            return None
