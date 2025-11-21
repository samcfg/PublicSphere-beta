"""
User contribution queries and reputation calculations.
Provides service layer for user analytics and profile metrics.
"""
from typing import Dict, List, Optional
from django.db.models import Q, Count, Subquery, OuterRef
from users.models import User, UserProfile, UserAttribution, UserModificationAttribution
from bookkeeper.models import ClaimVersion, SourceVersion, EdgeVersion


class UserContributionService:
    """Service for querying user contributions and calculating reputation"""

    @staticmethod
    def get_user_contributions(user_id: int) -> Dict[str, int]:
        """
        Get total contributions by entity type for a user.

        Returns:
            Dict with keys: total_claims, total_sources, total_connections, total_edits
        """
        # Original creations (from UserAttribution)
        attributions = UserAttribution.objects.filter(user_id=user_id).values('entity_type').annotate(
            count=Count('id')
        )

        contributions = {
            'total_claims': 0,
            'total_sources': 0,
            'total_connections': 0,
            'total_edits': 0
        }

        for attr in attributions:
            entity_type = attr['entity_type']
            count = attr['count']
            if entity_type == 'claim':
                contributions['total_claims'] = count
            elif entity_type == 'source':
                contributions['total_sources'] = count
            elif entity_type == 'connection':
                contributions['total_connections'] = count

        # Edits (from UserModificationAttribution)
        edits = UserModificationAttribution.objects.filter(user_id=user_id).count()
        contributions['total_edits'] = edits

        return contributions

    @staticmethod
    def update_user_profile_metrics(user_id: int) -> None:
        """
        Recalculate and update UserProfile metrics for a user.
        Called after contributions change.
        """
        try:
            profile = UserProfile.objects.get(user_id=user_id)
        except UserProfile.DoesNotExist:
            # Create profile if it doesn't exist
            profile = UserProfile.objects.create(user_id=user_id)

        contributions = UserContributionService.get_user_contributions(user_id)

        profile.total_claims = contributions['total_claims']
        profile.total_sources = contributions['total_sources']
        profile.total_connections = contributions['total_connections']
        profile.calculate_reputation()
        profile.save()

    @staticmethod
    def get_entity_creator(entity_uuid: str, entity_type: str) -> Optional[User]:
        """
        Get the original creator of an entity.

        Args:
            entity_uuid: UUID of the claim, source, or connection
            entity_type: 'claim', 'source', or 'connection'

        Returns:
            User instance or None if not found or deleted
        """
        try:
            attribution = UserAttribution.objects.get(
                entity_uuid=entity_uuid,
                entity_type=entity_type
            )
            return attribution.user
        except UserAttribution.DoesNotExist:
            return None

    @staticmethod
    def get_entity_editors(entity_uuid: str, entity_type: str) -> List[Dict]:
        """
        Get all users who have edited an entity, with version numbers.

        Args:
            entity_uuid: UUID of the claim, source, or connection
            entity_type: 'claim', 'source', or 'connection'

        Returns:
            List of dicts: [{'user': User, 'version_number': int, 'is_anonymous': bool}, ...]
        """
        modifications = UserModificationAttribution.objects.filter(
            entity_uuid=entity_uuid,
            entity_type=entity_type
        ).select_related('user').order_by('version_number')

        return [
            {
                'user': mod.user,
                'version_number': mod.version_number,
                'is_anonymous': mod.is_anonymous,
                'timestamp': mod.timestamp
            }
            for mod in modifications
        ]

    @staticmethod
    def get_user_created_entities(user_id: int) -> Dict:
        """
        Get all entities created by a user with their content.

        Args:
            user_id: User ID

        Returns:
            Dict with keys: claims, sources, connections
            Each containing list of entity dicts with content and attribution info
        """
        # Get all attributions for user, grouped by type
        attributions = UserAttribution.objects.filter(user_id=user_id)

        claim_attrs = {a.entity_uuid: a for a in attributions.filter(entity_type='claim')}
        source_attrs = {a.entity_uuid: a for a in attributions.filter(entity_type='source')}
        connection_attrs = {a.entity_uuid: a for a in attributions.filter(entity_type='connection')}

        # Helper to get latest version via subquery
        def get_latest_versions(model, id_field, uuids):
            if not uuids:
                return []
            # Subquery to find max version_number for each entity
            latest_version_subq = model.objects.filter(
                **{id_field: OuterRef(id_field)}
            ).order_by('-version_number').values('version_number')[:1]

            return model.objects.filter(
                **{f'{id_field}__in': uuids},
                version_number=Subquery(latest_version_subq)
            )

        # Fetch latest versions for each type
        claim_versions = get_latest_versions(ClaimVersion, 'node_id', list(claim_attrs.keys()))
        source_versions = get_latest_versions(SourceVersion, 'node_id', list(source_attrs.keys()))
        edge_versions = get_latest_versions(EdgeVersion, 'edge_id', list(connection_attrs.keys()))

        # Build node lookup for resolving connection endpoints
        # Collect all node IDs referenced by connections
        endpoint_ids = set()
        for edge in edge_versions:
            endpoint_ids.add(edge.source_node_id)
            endpoint_ids.add(edge.target_node_id)

        # Fetch latest versions of all endpoint nodes
        node_lookup = {}
        if endpoint_ids:
            # Check claims
            claim_endpoint_subq = ClaimVersion.objects.filter(
                node_id=OuterRef('node_id')
            ).order_by('-version_number').values('version_number')[:1]

            for claim in ClaimVersion.objects.filter(
                node_id__in=endpoint_ids,
                version_number=Subquery(claim_endpoint_subq)
            ):
                node_lookup[claim.node_id] = {
                    'type': 'claim',
                    'display': claim.content[:100] if claim.content else '[No content]'
                }

            # Check sources
            source_endpoint_subq = SourceVersion.objects.filter(
                node_id=OuterRef('node_id')
            ).order_by('-version_number').values('version_number')[:1]

            for source in SourceVersion.objects.filter(
                node_id__in=endpoint_ids,
                version_number=Subquery(source_endpoint_subq)
            ):
                node_lookup[source.node_id] = {
                    'type': 'source',
                    'display': source.title or source.url or '[No title]'
                }

        # Build response
        claims = []
        for claim in claim_versions:
            attr = claim_attrs.get(claim.node_id)
            claims.append({
                'uuid': claim.node_id,
                'content': claim.content,
                'is_anonymous': attr.is_anonymous if attr else False,
                'created_at': attr.timestamp.isoformat() if attr else None,
            })

        sources = []
        for source in source_versions:
            attr = source_attrs.get(source.node_id)
            sources.append({
                'uuid': source.node_id,
                'title': source.title,
                'url': source.url,
                'author': source.author,
                'source_type': source.source_type,
                'is_anonymous': attr.is_anonymous if attr else False,
                'created_at': attr.timestamp.isoformat() if attr else None,
            })

        connections = []
        for edge in edge_versions:
            attr = connection_attrs.get(edge.edge_id)
            source_node = node_lookup.get(edge.source_node_id, {'type': 'unknown', 'display': '[Unknown]'})
            target_node = node_lookup.get(edge.target_node_id, {'type': 'unknown', 'display': '[Unknown]'})

            connections.append({
                'uuid': edge.edge_id,
                'source_node_id': edge.source_node_id,
                'source_node_type': source_node['type'],
                'source_node_display': source_node['display'],
                'target_node_id': edge.target_node_id,
                'target_node_type': target_node['type'],
                'target_node_display': target_node['display'],
                'notes': edge.notes,
                'logic_type': edge.logic_type,
                'is_anonymous': attr.is_anonymous if attr else False,
                'created_at': attr.timestamp.isoformat() if attr else None,
            })

        return {
            'claims': claims,
            'sources': sources,
            'connections': connections,
        }

    @staticmethod
    def get_user_edited_entities(user_id: int, entity_type: Optional[str] = None) -> List[str]:
        """
        Get list of entity UUIDs edited by a user (excludes original creations).

        Args:
            user_id: User ID
            entity_type: Optional filter by 'claim', 'source', or 'connection'

        Returns:
            List of unique entity UUIDs
        """
        query = UserModificationAttribution.objects.filter(user_id=user_id)
        if entity_type:
            query = query.filter(entity_type=entity_type)

        return list(query.values_list('entity_uuid', flat=True).distinct())

    @staticmethod
    def toggle_anonymity(entity_uuid: str, entity_type: str, user_id: int,
                        version_number: Optional[int] = None) -> bool:
        """
        Toggle anonymity for a user's contribution (original creation or specific edit).

        Args:
            entity_uuid: UUID of entity
            entity_type: 'claim', 'source', or 'connection'
            user_id: User making the request (must match attribution owner)
            version_number: If None, toggles original creation; if int, toggles that edit

        Returns:
            True if toggled successfully, False if not found or unauthorized
        """
        if version_number is None:
            # Toggle original creation anonymity
            try:
                attribution = UserAttribution.objects.get(
                    entity_uuid=entity_uuid,
                    entity_type=entity_type,
                    user_id=user_id
                )
                attribution.is_anonymous = not attribution.is_anonymous
                attribution.save()
                return True
            except UserAttribution.DoesNotExist:
                return False
        else:
            # Toggle edit anonymity
            try:
                modification = UserModificationAttribution.objects.get(
                    entity_uuid=entity_uuid,
                    entity_type=entity_type,
                    version_number=version_number,
                    user_id=user_id
                )
                modification.is_anonymous = not modification.is_anonymous
                modification.save()
                return True
            except UserModificationAttribution.DoesNotExist:
                return False

    @staticmethod
    def get_leaderboard(limit: int = 100) -> List[Dict]:
        """
        Get top contributors by reputation score.

        Args:
            limit: Maximum number of users to return

        Returns:
            List of dicts with user info and metrics
        """
        profiles = UserProfile.objects.select_related('user').order_by('-reputation_score')[:limit]

        return [
            {
                'username': profile.user.username,
                'reputation_score': profile.reputation_score,
                'total_claims': profile.total_claims,
                'total_sources': profile.total_sources,
                'total_connections': profile.total_connections,
                'joined_date': profile.user.date_joined
            }
            for profile in profiles
        ]


def get_contribution_service() -> UserContributionService:
    """Get the contribution service instance"""
    return UserContributionService()
