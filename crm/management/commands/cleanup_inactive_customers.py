from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, datetime
from crm.models import Customer, Order
from django.db.models import Q, Max
from django.db import connection

class Command(BaseCommand):
    help = 'Cleans up inactive customers who have not placed an order in over a year'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reference-date',
            type=str,
            help='Reference date for testing (format: YYYY-MM-DD)',
            required=False
        )

    def handle(self, *args, **options):
        # Use reference date if provided, otherwise use current time
        if options.get('reference_date'):
            current_time = timezone.make_aware(datetime.strptime(options['reference_date'], '%Y-%m-%d'))
        else:
            current_time = timezone.now()

        # Calculate the date one year ago
        one_year_ago = current_time - timedelta(days=365)
        self.stdout.write(f"Reference time: {current_time}")
        self.stdout.write(f"One year ago: {one_year_ago}")

        # Print all customers and their latest order dates for debugging
        self.stdout.write("\nAll customers and their latest order dates:")
        for customer in Customer.objects.all():
            latest_order = customer.orders.order_by('-order_date').first()
            if latest_order:
                self.stdout.write(f"Customer: {customer.name}, Latest order: {latest_order.order_date} (Is before one year ago? {latest_order.order_date < one_year_ago})")
            else:
                self.stdout.write(f"Customer: {customer.name}, No orders")

        # Find customers with their latest order date using raw SQL
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT c.id, c.name, MAX(o.order_date) as latest_order
                FROM crm_customer c
                LEFT JOIN crm_order o ON c.id = o.customer_id
                GROUP BY c.id, c.name
                HAVING MAX(o.order_date) < %s OR MAX(o.order_date) IS NULL
            """, [one_year_ago])
            inactive_customer_ids = [row[0] for row in cursor.fetchall()]

        # Get the queryset of inactive customers
        inactive_customers = Customer.objects.filter(id__in=inactive_customer_ids)

        # Print inactive customers for debugging
        self.stdout.write("\nInactive customers:")
        for customer in inactive_customers:
            latest_order = customer.orders.order_by('-order_date').first()
            if latest_order:
                self.stdout.write(f"Customer: {customer.name}, Latest order: {latest_order.order_date}")
            else:
                self.stdout.write(f"Customer: {customer.name}, No orders")

        # Count and delete inactive customers
        count = inactive_customers.count()
        self.stdout.write(f"\nDeleting {count} inactive customers")
        
        # Delete inactive customers
        deleted_count = inactive_customers.delete()[0]

        # Get current timestamp
        timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S')

        # Log the results
        with open('/tmp/customer_cleanup_log.txt', 'a') as f:
            f.write(f'{current_time.strftime("%c")}: Deleted {deleted_count} inactive customers\n') 