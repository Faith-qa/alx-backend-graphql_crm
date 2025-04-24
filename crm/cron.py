from datetime import datetime
import os
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

def log_crm_heartbeat():
    """
    Log a heartbeat message and verify GraphQL endpoint responsiveness.
    Logs to /tmp/crm_heartbeat_log.txt in the format DD/MM/YYYY-HH:MM:SS CRM is alive
    """
    timestamp = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    log_message = f"{timestamp} CRM is alive\n"
    
    try:
        # Set up GraphQL client
        transport = RequestsHTTPTransport(url='http://localhost:8000/graphql')
        client = Client(transport=transport, fetch_schema_from_transport=True)
        
        # Query the hello field
        query = gql("""
            query {
                hello
            }
        """)
        
        # Execute query
        result = client.execute(query)
        if result.get('hello'):
            log_message = f"{timestamp} CRM is alive (GraphQL endpoint responsive)\n"
    except Exception as e:
        log_message = f"{timestamp} CRM is alive (GraphQL check failed: {str(e)})\n"
    
    # Ensure log directory exists
    os.makedirs(os.path.dirname('/tmp/crm_heartbeat_log.txt'), exist_ok=True)
    
    # Append heartbeat message to log file
    with open('/tmp/crm_heartbeat_log.txt', 'a') as f:
        f.write(log_message) 