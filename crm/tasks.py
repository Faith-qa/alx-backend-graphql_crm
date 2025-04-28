import os
from datetime import datetime
from celery import shared_task
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

@shared_task
def generate_crm_report():
    """
    Generate a weekly CRM report using GraphQL queries and log it to a file.
    """
    # GraphQL query to fetch CRM statistics
    query = gql("""
        query {
            totalCustomers
            totalOrders
            totalRevenue
        }
    """)
    
    # Create GraphQL client
    transport = RequestsHTTPTransport(
        url='http://localhost:8000/graphql/',
        verify=True,
        retries=3,
    )
    client = Client(transport=transport, fetch_schema_from_transport=True)
    
    try:
        # Execute the query
        result = client.execute(query)
        
        # Format the report message
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        report = (
            f"{timestamp} - Report: "
            f"{result['totalCustomers']} customers, "
            f"{result['totalOrders']} orders, "
            f"${result['totalRevenue']:.2f} revenue\n"
        )
        
        # Log the report to file
        log_file = '/tmp/crm_report_log.txt'
        with open(log_file, 'a') as f:
            f.write(report)
            
        return f"Report generated successfully: {report}"
        
    except Exception as e:
        error_msg = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Error generating report: {str(e)}\n"
        with open('/tmp/crm_report_log.txt', 'a') as f:
            f.write(error_msg)
        raise 