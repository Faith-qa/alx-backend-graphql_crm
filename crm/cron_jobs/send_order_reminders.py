#!/usr/bin/env python3
import os
import sys
from datetime import datetime, timedelta
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# Default log file path
DEFAULT_LOG_FILE = '/tmp/order_reminders_log.txt'

# Set up the GraphQL client
transport = RequestsHTTPTransport(url='http://localhost:8000/graphql')
client = Client(transport=transport, fetch_schema_from_transport=True)

# GraphQL query to get recent orders
query = gql("""
    query GetRecentOrders($lastWeek: DateTime!) {
        orders(orderDate_Gte: $lastWeek) {
            edges {
                node {
                    id
                    orderDate
                    customer {
                        email
                    }
                }
            }
        }
    }
""")

def process_orders(log_file=DEFAULT_LOG_FILE):
    """Process orders and log reminders to the specified file."""
    # Calculate date 7 days ago
    last_week = datetime.now() - timedelta(days=7)
    
    try:
        # Execute the query
        result = client.execute(query, variable_values={
            'lastWeek': last_week.isoformat()
        })
        
        # Get current timestamp for logging
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Process orders and log reminders
        with open(log_file, 'a') as f:
            f.write(f"\n=== Order Reminders {timestamp} ===\n")
            
            for edge in result['orders']['edges']:
                order = edge['node']
                log_entry = f"{timestamp}: Order {order['id']} - Customer: {order['customer']['email']}\n"
                f.write(log_entry)
        
        print("Order reminders processed!")
        return True
        
    except Exception as e:
        print(f"Error processing order reminders: {str(e)}", file=sys.stderr)
        return False

def main():
    """Main entry point for the script."""
    success = process_orders()
    if not success:
        sys.exit(1)

if __name__ == '__main__':
    main() 