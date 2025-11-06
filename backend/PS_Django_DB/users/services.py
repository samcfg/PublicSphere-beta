"""
User contribution queries and reputation calculations.
Provides service layer for user analytics and profile metrics.
"""
from typing import Dict, List, Optional
from django.db.models import Q, Count
from users.models import User, UserProfile, UserAttribution, UserModificationAttribution


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
    def get_user_created_entities(user_id: int, entity_type: Optional[str] = None) -> List[str]:
        """
        Get list of entity UUIDs created by a user.

        Args:
            user_id: User ID
            entity_type: Optional filter by 'claim', 'source', or 'connection'

        Returns:
            List of entity UUIDs
        """
        query = UserAttribution.objects.filter(user_id=user_id)
        if entity_type:
            query = query.filter(entity_type=entity_type)

        return list(query.values_list('entity_uuid', flat=True))

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
