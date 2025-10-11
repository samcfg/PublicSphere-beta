from PS_Graph_DB.src.language import get_language_ops
from datetime import datetime, timedelta
from django.utils import timezone

def main():
    ops = get_language_ops()
    ops.set_graph("test_graph")
    print("Graph set to 'test_graph'")
    print("\nAvailable commands:")
    print("  ops.create_claim(content='...')")
    print("  ops.delete_node('uuid')")
    print("  ops.get_nodes_at_timestamp(timestamp)")
    print("\nTimezone helpers (already imported):")
    print("  timezone.now()  - current UTC time")
    print("  timezone.now() - timedelta(minutes=40)  - 40 minutes ago")
    print("  datetime(2025, 10, 10, 20, 30)  - create naive datetime")
    print("  timezone.make_aware(datetime(...))  - convert to UTC")

    # Make imports available in interactive session
    import code
    namespace = {
        'ops': ops,
        'datetime': datetime,
        'timedelta': timedelta,
        'timezone': timezone
    }
    code.interact(local=namespace)

if __name__ == "__main__":
    main()