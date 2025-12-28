"""
Management command to sync missing nodes from AGE to Django bookkeeper tables.

Usage: uv run python manage.py sync_age_to_django
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from bookkeeper.models import ClaimVersion, SourceVersion
from PS_Graph_DB.src.language import get_language_ops


class Command(BaseCommand):
    help = 'Sync missing nodes from AGE graph database to Django bookkeeper tables'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        ops = get_language_ops()
        ops.set_graph('test_graph')

        # Sync Claims
        self.stdout.write('\n=== Syncing Claims ===')
        age_claims = ops.get_all_claims()
        django_node_ids = set(
            ClaimVersion.objects.filter(valid_to__isnull=True).values_list('node_id', flat=True)
        )

        claims_synced = 0
        for claim_wrapper in age_claims:
            props = claim_wrapper.get('claim', {}).get('properties', {})
            node_id = props.get('id')
            content = props.get('content', '')

            if node_id not in django_node_ids:
                self.stdout.write(f'  Missing claim: {node_id}')
                self.stdout.write(f'    Content: {content[:80]}...')

                if not dry_run:
                    ClaimVersion.objects.create(
                        node_id=node_id,
                        content=content,
                        version_number=1,
                        operation='CREATE',
                        timestamp=timezone.now(),
                        valid_from=timezone.now(),
                        valid_to=None,
                        changed_by='sync_script',
                        change_notes='Backfilled from AGE database'
                    )
                    self.stdout.write(self.style.SUCCESS(f'    ✓ Synced to Django'))
                    claims_synced += 1
                else:
                    self.stdout.write(self.style.WARNING(f'    Would sync (dry run)'))

        # Sync Sources
        self.stdout.write('\n=== Syncing Sources ===')
        age_sources = ops.get_all_sources()
        django_source_ids = set(
            SourceVersion.objects.filter(valid_to__isnull=True).values_list('node_id', flat=True)
        )

        sources_synced = 0
        for source_wrapper in age_sources:
            props = source_wrapper.get('source', {}).get('properties', {})
            node_id = props.get('id')
            url = props.get('url', '')
            title = props.get('title', '')
            author = props.get('author')
            publication_date = props.get('publication_date')
            source_type = props.get('source_type')
            content = props.get('content', '')

            if node_id not in django_source_ids:
                self.stdout.write(f'  Missing source: {node_id}')
                self.stdout.write(f'    Title: {title[:80]}...')

                if not dry_run:
                    SourceVersion.objects.create(
                        node_id=node_id,
                        url=url,
                        title=title,
                        author=author,
                        publication_date=publication_date,
                        source_type=source_type,
                        content=content,
                        version_number=1,
                        operation='CREATE',
                        timestamp=timezone.now(),
                        valid_from=timezone.now(),
                        valid_to=None,
                        changed_by='sync_script',
                        change_notes='Backfilled from AGE database'
                    )
                    self.stdout.write(self.style.SUCCESS(f'    ✓ Synced to Django'))
                    sources_synced += 1
                else:
                    self.stdout.write(self.style.WARNING(f'    Would sync (dry run)'))

        # Summary
        self.stdout.write('\n' + '='*50)
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN COMPLETE - No changes made'))
        else:
            self.stdout.write(self.style.SUCCESS(f'SYNC COMPLETE'))
            self.stdout.write(f'  Claims synced: {claims_synced}')
            self.stdout.write(f'  Sources synced: {sources_synced}')
            self.stdout.write('\nSearch functionality should now work for all nodes.')
