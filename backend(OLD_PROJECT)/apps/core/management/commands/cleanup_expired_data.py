# File: backend/apps/core/management/commands/cleanup_expired_data.py
import os
import glob
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.core.management import call_command
import logging

logger = logging.getLogger('apps.cleanup')

class Command(BaseCommand):
    help = 'Clean up expired data per GDPR retention periods'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be deleted'))
        
        self.stdout.write('Starting data cleanup...')
        
        try:
            self.cleanup_sessions(dry_run)
            self.cleanup_logs(dry_run)
            
            self.stdout.write(self.style.SUCCESS('Data cleanup completed successfully'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Data cleanup failed: {e}'))
            raise
    
    def cleanup_sessions(self, dry_run):
        """Clean expired Django sessions"""
        self.stdout.write('Cleaning expired sessions...')
        
        if not dry_run:
            call_command('clearsessions')
        else:
            from django.contrib.sessions.models import Session
            expired_count = Session.objects.filter(expire_date__lt=timezone.now()).count()
            self.stdout.write(f'  Would delete {expired_count} expired sessions')
    
    def cleanup_logs(self, dry_run):
        """Clean old log files based on retention periods"""
        self.stdout.write('Cleaning old log files...')
        
        # Use default log directory
        log_dir = settings.BASE_DIR / 'logs'
        if not os.path.exists(log_dir):
            self.stdout.write('  No log directory found, skipping')
            return
        
        retention_periods = getattr(settings, 'GDPR_RETENTION_PERIODS', {})
        now = datetime.now()
        
        # Define log file patterns and their retention periods
        log_patterns = {
            'django*.log*': retention_periods.get('django_application_logs', timedelta(days=90)),
            'error*.log*': retention_periods.get('django_error_logs', timedelta(days=180)),
            'auth*.log*': retention_periods.get('authentication_logs', timedelta(days=30)),
            'middleware*.log*': retention_periods.get('middleware_logs', timedelta(days=30)),
        }
        
        total_deleted = 0
        
        for pattern, retention_period in log_patterns.items():
            if not retention_period:
                continue
                
            cutoff_date = now - retention_period
            log_files = glob.glob(os.path.join(log_dir, pattern))
            pattern_deleted = 0
            
            for log_file in log_files:
                try:
                    file_modified = datetime.fromtimestamp(os.path.getmtime(log_file))
                    if file_modified < cutoff_date:
                        if not dry_run:
                            os.remove(log_file)
                            pattern_deleted += 1
                        else:
                            self.stdout.write(f'  Would delete: {log_file}')
                            pattern_deleted += 1
                            
                except OSError as e:
                    self.stdout.write(f'  Warning: Could not process {log_file}: {e}')
            
            total_deleted += pattern_deleted
            if pattern_deleted > 0:
                action = "Would delete" if dry_run else "Deleted"
                self.stdout.write(f'  {action} {pattern_deleted} files matching {pattern}')
        
        if total_deleted == 0:
            self.stdout.write('  No old log files found to clean up')