from PS_Graph_DB.src.language import get_language_ops
from datetime import datetime, timedelta
from django.utils import timezone
import os
import sys
import django

# Django setup for User access
django_path = os.path.join(os.path.dirname(__file__), 'PS_Django_DB')
sys.path.insert(0, django_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User

def main():
    ops = get_language_ops()
    ops.set_graph("test_graph")
    print("Graph set to 'test_graph'")
    print("\nAvailable commands:")
    print("  ops.create_claim(content='...', user_id=1)")
    print("  ops.create_source(url='...', title='...', user_id=1)")
    print("  ops.delete_node('uuid', user_id=1)")
    print("  ops.get_nodes_at_timestamp(timestamp)")
    print("\nTimezone helpers (already imported):")
    print("  timezone.now()  - current UTC time")
    print("  timezone.now() - timedelta(minutes=40)  - 40 minutes ago")
    print("  datetime(2025, 10, 10, 20, 30)  - create naive datetime")
    print("  timezone.make_aware(datetime(...))  - convert to UTC")
    print("\nUser helpers (already imported):")
    print("  User.objects.all().values_list('id', 'username')  - list all users")
    print("  User.objects.get(username='sam').id  - get user ID")

    # Make imports available in interactive session
    import code
    namespace = {
        'ops': ops,
        'datetime': datetime,
        'timedelta': timedelta,
        'timezone': timezone,
        'User': User
    }
    code.interact(local=namespace)

if __name__ == "__main__":
    main()