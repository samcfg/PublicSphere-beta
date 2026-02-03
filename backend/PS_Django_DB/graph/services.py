"""
Services for search and deduplication operations on graph nodes.

These services query the Django bookkeeper tables (ClaimVersion, SourceVersion)
rather than AGE, since all attribute-based queries belong in relational DB.
"""

from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import Q, F
from bookkeeper.models import ClaimVersion, SourceVersion
from .utils import normalize_url, normalize_content


class DeduplicationService:
    """
    Duplicate detection for graph nodes before creation.

    Uses high similarity thresholds (0.85+) to minimize false positives.
    Only warns when highly confident it's a duplicate.
    """

    SIMILARITY_THRESHOLD = 0.85  # High threshold to avoid false positives

    @staticmethod
    def check_duplicate_claim(content: str) -> dict | None:
        """
        Duplicate detection for claims.

        Args:
            content: Claim content to check

        Returns:
            {
                'duplicate_type': 'exact' | 'similar',
                'existing_id': str (node_id),
                'existing_content': str,
                'similarity_score': float  # For 'similar' type only
            } or None if no duplicate found

        Matching strategy:
            1. Exact match on content_normalized (highest priority)
            2. Trigram similarity > 0.85 (typos, minor variations)
        """
        if not content or not content.strip():
            return None

        content_norm = normalize_content(content)

        # 1. Check exact match
        exact_match = ClaimVersion.objects.filter(
            content_normalized=content_norm,
            valid_to__isnull=True  # Current versions only
        ).first()

        if exact_match:
            return {
                'duplicate_type': 'exact',
                'existing_id': exact_match.node_id,
                'existing_content': exact_match.content,
            }

        # 2. Check trigram similarity
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT node_id, content, similarity(content, %s) as sim
                FROM claim_versions
                WHERE valid_to IS NULL
                  AND similarity(content, %s) > %s
                ORDER BY sim DESC
                LIMIT 1
            """, [content, content, DeduplicationService.SIMILARITY_THRESHOLD])

            row = cursor.fetchone()
            if row:
                return {
                    'duplicate_type': 'similar',
                    'existing_id': row[0],
                    'existing_content': row[1],
                    'similarity_score': row[2],
                }

        return None

    @staticmethod
    def check_duplicate_source(url: str = None, title: str = None, doi: str = None) -> dict | None:
        """
        Four-tier source deduplication.

        Args:
            url: Source URL (optional)
            title: Source title (required)
            doi: Digital Object Identifier (optional, highest priority)

        Returns:
            {
                'duplicate_type': 'doi' | 'url' | 'title_exact' | 'title_similar',
                'existing_id': str (node_id),
                'existing_title': str,
                'existing_url': str,
                'existing_doi': str,
                'similarity_score': float  # For 'title_similar' only
            } or None if no duplicate found

        Matching strategy (in order):
            1. DOI normalized match (highest priority - globally unique identifier)
            2. URL normalized match (hard block - same document)
            3. Title exact match on title_normalized
            4. Title trigram similarity > 0.85 (catches typos like "IPCC 2021" vs "IPCC Report 2021")

        Note: Source content field is NOT checked - it's user's personal summary.
        """
        from .utils import normalize_doi

        # 1. DOI deduplication (highest priority)
        if doi:
            doi_norm = normalize_doi(doi)
            if doi_norm:
                duplicate = SourceVersion.objects.filter(
                    doi_normalized=doi_norm,
                    valid_to__isnull=True
                ).first()

                if duplicate:
                    return {
                        'duplicate_type': 'doi',
                        'existing_id': duplicate.node_id,
                        'existing_title': duplicate.title,
                        'existing_url': duplicate.url,
                        'existing_doi': duplicate.doi,
                    }

        # 2. URL deduplication
        if url:
            url_norm = normalize_url(url)
            if url_norm:
                # Query current versions only (valid_to IS NULL)
                duplicate = SourceVersion.objects.filter(
                    url_normalized=url_norm,
                    valid_to__isnull=True
                ).first()

                if duplicate:
                    return {
                        'duplicate_type': 'url',
                        'existing_id': duplicate.node_id,
                        'existing_title': duplicate.title,
                        'existing_url': duplicate.url,
                    }

        # 2. Title-based deduplication (Phase 2)
        if title and title.strip():
            title_norm = normalize_content(title)

            # Check exact match on normalized title
            exact_match = SourceVersion.objects.filter(
                title_normalized=title_norm,
                valid_to__isnull=True
            ).first()

            if exact_match:
                return {
                    'duplicate_type': 'title_exact',
                    'existing_id': exact_match.node_id,
                    'existing_title': exact_match.title,
                    'existing_url': exact_match.url,
                }

            # Check trigram similarity on title
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT node_id, title, url, similarity(title, %s) as sim
                    FROM source_versions
                    WHERE valid_to IS NULL
                      AND similarity(title, %s) > %s
                    ORDER BY sim DESC
                    LIMIT 1
                """, [title, title, DeduplicationService.SIMILARITY_THRESHOLD])

                row = cursor.fetchone()
                if row:
                    return {
                        'duplicate_type': 'title_similar',
                        'existing_id': row[0],
                        'existing_title': row[1],
                        'existing_url': row[2],
                        'similarity_score': row[3],
                    }

        return None


class SearchService:
    """
    Full-text search for graph nodes.

    Uses PostgreSQL full-text search + trigram matching for broad discovery.
    Lower threshold (0.3) than deduplication to cast wide net.
    """

    SEARCH_SIMILARITY_THRESHOLD = 0.3  # Broad search - show anything potentially relevant

    @staticmethod
    def search_nodes(query: str, node_type: str = None) -> list:
        """
        Search current node versions using combined full-text + trigram + substring matching.

        Args:
            query: Search string
            node_type: 'claim' | 'source' | None (both)

        Returns:
            List of {
                'id': str (node_id),
                'node_type': 'claim' | 'source',
                'content': str (for claims) or None,
                'title': str (for sources) or None,
                'url': str (for sources, if present) or None,
                'rank': float (relevance score - higher is better)
            }

        Strategy:
            1. Full-text search (linguistic understanding, stemming)
            2. Trigram similarity (typo tolerance, fuzzy matching)
            3. Substring matching (ILIKE for finding queries within long content)
            4. Combine results, deduplicate, rank by best score
        """
        if not query or not query.strip():
            return []

        from django.db import connection
        results_dict = {}  # {node_id: {node data with best rank}}

        # ========== SEARCH CLAIMS ==========
        if not node_type or node_type == 'claim':
            # 1. Full-text search on claims
            search_query = SearchQuery(query, config='english')
            claims_fulltext = ClaimVersion.objects.filter(
                valid_to__isnull=True,
                content_search=search_query
            ).annotate(
                rank=SearchRank(F('content_search'), search_query)
            ).order_by('-rank')[:30]

            for claim in claims_fulltext:
                results_dict[str(claim.node_id)] = {
                    'id': str(claim.node_id),
                    'node_type': 'claim',
                    'content': claim.content,
                    'title': None,
                    'url': None,
                    'rank': float(claim.rank),
                }

            # 2. Trigram similarity search on claims
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT node_id, content, similarity(content, %s) as sim
                    FROM claim_versions
                    WHERE valid_to IS NULL
                      AND similarity(content, %s) > %s
                    ORDER BY sim DESC
                    LIMIT 30
                """, [query, query, SearchService.SEARCH_SIMILARITY_THRESHOLD])

                for row in cursor.fetchall():
                    node_id_str = str(row[0])
                    trigram_rank = float(row[2])

                    # If already in results from full-text, keep the higher rank
                    if node_id_str in results_dict:
                        results_dict[node_id_str]['rank'] = max(
                            results_dict[node_id_str]['rank'],
                            trigram_rank
                        )
                    else:
                        results_dict[node_id_str] = {
                            'id': node_id_str,
                            'node_type': 'claim',
                            'content': row[1],
                            'title': None,
                            'url': None,
                            'rank': trigram_rank,
                        }

            # 3. Substring matching on claims (ILIKE for long content)
            # Rank boost for substring matches: higher if query appears earlier or is larger portion
            substring_claims = ClaimVersion.objects.filter(
                valid_to__isnull=True,
                content__icontains=query
            )[:30]

            for claim in substring_claims:
                node_id_str = str(claim.node_id)
                # Calculate rank based on query position and content length
                # Earlier position and larger query/content ratio = higher rank
                content_lower = claim.content.lower()
                query_lower = query.lower()
                position = content_lower.find(query_lower)

                # Rank formula: base 0.5 + bonuses for position and query coverage
                position_bonus = max(0, 0.3 * (1 - position / len(claim.content)))
                coverage_bonus = min(0.2, len(query) / len(claim.content))
                substring_rank = 0.5 + position_bonus + coverage_bonus

                # If already in results, keep the higher rank
                if node_id_str in results_dict:
                    results_dict[node_id_str]['rank'] = max(
                        results_dict[node_id_str]['rank'],
                        substring_rank
                    )
                else:
                    results_dict[node_id_str] = {
                        'id': node_id_str,
                        'node_type': 'claim',
                        'content': claim.content,
                        'title': None,
                        'url': None,
                        'rank': substring_rank,
                    }

        # ========== SEARCH SOURCES ==========
        if not node_type or node_type == 'source':
            # 1. Full-text search on sources (title field)
            search_query = SearchQuery(query, config='english')
            sources_fulltext = SourceVersion.objects.filter(
                valid_to__isnull=True,
                title_search=search_query
            ).annotate(
                rank=SearchRank(F('title_search'), search_query)
            ).order_by('-rank')[:30]

            for source in sources_fulltext:
                results_dict[str(source.node_id)] = {
                    'id': str(source.node_id),
                    'node_type': 'source',
                    'content': None,
                    'title': source.title,
                    'url': source.url,
                    'rank': float(source.rank),
                }

            # 2. Trigram similarity search on sources (title field)
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT node_id, title, url, similarity(title, %s) as sim
                    FROM source_versions
                    WHERE valid_to IS NULL
                      AND similarity(title, %s) > %s
                    ORDER BY sim DESC
                    LIMIT 30
                """, [query, query, SearchService.SEARCH_SIMILARITY_THRESHOLD])

                for row in cursor.fetchall():
                    node_id_str = str(row[0])
                    trigram_rank = float(row[3])

                    # If already in results from full-text, keep the higher rank
                    if node_id_str in results_dict:
                        results_dict[node_id_str]['rank'] = max(
                            results_dict[node_id_str]['rank'],
                            trigram_rank
                        )
                    else:
                        results_dict[node_id_str] = {
                            'id': node_id_str,
                            'node_type': 'source',
                            'content': None,
                            'title': row[1],
                            'url': row[2],
                            'rank': trigram_rank,
                        }

            # 3. Substring matching on sources (ILIKE for long titles)
            substring_sources = SourceVersion.objects.filter(
                valid_to__isnull=True,
                title__icontains=query
            )[:30]

            for source in substring_sources:
                node_id_str = str(source.node_id)
                # Calculate rank based on query position and title length
                title_lower = source.title.lower()
                query_lower = query.lower()
                position = title_lower.find(query_lower)

                # Rank formula: base 0.5 + bonuses for position and query coverage
                position_bonus = max(0, 0.3 * (1 - position / len(source.title)))
                coverage_bonus = min(0.2, len(query) / len(source.title))
                substring_rank = 0.5 + position_bonus + coverage_bonus

                # If already in results, keep the higher rank
                if node_id_str in results_dict:
                    results_dict[node_id_str]['rank'] = max(
                        results_dict[node_id_str]['rank'],
                        substring_rank
                    )
                else:
                    results_dict[node_id_str] = {
                        'id': node_id_str,
                        'node_type': 'source',
                        'content': None,
                        'title': source.title,
                        'url': source.url,
                        'rank': substring_rank,
                    }

        # Convert dict to list and sort by rank (highest first)
        results = list(results_dict.values())
        results.sort(key=lambda x: x['rank'], reverse=True)

        return results[:40]  # Return top 40 overall

    @staticmethod
    def search_historical_versions(query: str, node_type: str = None, limit: int = 3) -> list:
        """
        Search ONLY historical/deleted versions (valid_to IS NOT NULL).

        Returns past versions that are no longer current but match the search.
        Useful for "from the archives" section in search results.

        Args:
            query: Search string
            node_type: 'claim' | 'source' | None (both)
            limit: Max results (default 3 for compact display)

        Returns:
            List of {id, node_type, content/title, version_number, timestamp, rank}
        """
        if not query or not query.strip():
            return []

        results = []

        # Search historical claim versions only
        if not node_type or node_type == 'claim':
            search_query = SearchQuery(query, config='english')

            claims = ClaimVersion.objects.filter(
                content_search=search_query,
                valid_to__isnull=False  # Only historical versions
            ).annotate(
                rank=SearchRank(F('content_search'), search_query)
            ).order_by('-rank')[:limit]

            for claim in claims:
                results.append({
                    'id': claim.node_id,
                    'node_type': 'claim',
                    'content': claim.content,
                    'title': None,
                    'url': None,
                    'rank': float(claim.rank),
                    'version_number': claim.version_number,
                    'timestamp': claim.valid_from.isoformat(),
                    'operation': claim.operation,  # CREATE, UPDATE, or DELETE
                })

        # Search historical source versions only
        if not node_type or node_type == 'source':
            search_query = SearchQuery(query, config='english')

            sources = SourceVersion.objects.filter(
                title_search=search_query,
                valid_to__isnull=False  # Only historical versions
            ).annotate(
                rank=SearchRank(F('title_search'), search_query)
            ).order_by('-rank')[:limit]

            for source in sources:
                results.append({
                    'id': source.node_id,
                    'node_type': 'source',
                    'content': None,
                    'title': source.title,
                    'url': source.url,
                    'rank': float(source.rank),
                    'version_number': source.version_number,
                    'timestamp': source.valid_from.isoformat(),
                    'operation': source.operation,
                })

        # Sort by rank and limit
        results.sort(key=lambda x: x['rank'], reverse=True)
        return results[:limit]

    @staticmethod
    def search_nodes_at_timestamp(query: str, timestamp, node_type: str = None) -> list:
        """
        Search graph as it existed at a specific timestamp.

        Args:
            query: Search string
            timestamp: datetime object - search nodes valid at this time
            node_type: 'claim' | 'source' | None (both)

        Returns:
            Same format as search_nodes() but filtered to versions valid at timestamp
        """
        if not query or not query.strip():
            return []

        results = []

        # Search claims valid at timestamp
        if not node_type or node_type == 'claim':
            search_query = SearchQuery(query, config='english')

            claims = ClaimVersion.objects.filter(
                valid_from__lte=timestamp,
                content_search=search_query
            ).filter(
                Q(valid_to__gt=timestamp) | Q(valid_to__isnull=True)
            ).annotate(
                rank=SearchRank(F('content_search'), search_query)
            ).order_by('-rank')[:20]

            for claim in claims:
                results.append({
                    'id': claim.node_id,
                    'node_type': 'claim',
                    'content': claim.content,
                    'title': None,
                    'url': None,
                    'rank': float(claim.rank),
                })

        # Search sources valid at timestamp (on title field)
        if not node_type or node_type == 'source':
            search_query = SearchQuery(query, config='english')

            sources = SourceVersion.objects.filter(
                valid_from__lte=timestamp,
                title_search=search_query
            ).filter(
                Q(valid_to__gt=timestamp) | Q(valid_to__isnull=True)
            ).annotate(
                rank=SearchRank(F('title_search'), search_query)
            ).order_by('-rank')[:20]

            for source in sources:
                results.append({
                    'id': source.node_id,
                    'node_type': 'source',
                    'content': None,
                    'title': source.title,
                    'url': source.url,
                    'rank': float(source.rank),
                })

        # Sort by rank
        results.sort(key=lambda x: x['rank'], reverse=True)

        return results[:40]
