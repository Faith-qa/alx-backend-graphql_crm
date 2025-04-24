import os
from datetime import datetime
from django.test import TestCase, Client
from unittest.mock import patch, mock_open
from crm.tasks import generate_crm_report
from crm.models import Customer, Product, Order
from decimal import Decimal
from crm.schema import schema

class CeleryReportTests(TestCase):
    def setUp(self):
        # Create test data
        self.customer = Customer.objects.create(
            name="Test Customer",
            email="test@example.com",
            phone="1234567890"
        )
        
        self.product = Product.objects.create(
            name="Test Product",
            price=Decimal("10.00"),
            stock=100
        )
        
        self.order = Order.objects.create(
            customer=self.customer,
            total_amount=Decimal("20.00")
        )
        self.order.products.add(self.product)
        
        # Set up test client
        self.client = Client()

    def tearDown(self):
        # Clean up test data
        Customer.objects.all().delete()
        Product.objects.all().delete()
        Order.objects.all().delete()
        
        # Clean up log file if it exists
        log_file = '/tmp/crm_report_log.txt'
        if os.path.exists(log_file):
            os.remove(log_file)

    @patch('gql.Client.execute')
    def test_generate_crm_report_success(self, mock_execute):
        """Test successful report generation"""
        # Mock GraphQL response
        mock_execute.return_value = {
            'totalCustomers': 1,
            'totalOrders': 1,
            'totalRevenue': 20.00
        }
        
        # Mock file operations
        mock_file = mock_open()
        with patch('builtins.open', mock_file):
            # Execute the task
            result = generate_crm_report()
            
            # Verify file was opened for appending
            mock_file.assert_called_with('/tmp/crm_report_log.txt', 'a')
            
            # Get the written content
            handle = mock_file()
            written_content = ''.join(call[0][0] for call in handle.write.call_args_list)
            
            # Verify log content format
            self.assertRegex(
                written_content,
                r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} - Report: 1 customers, 1 orders, \$20.00 revenue\n',
                "Log message should match expected format"
            )
            
            # Verify return value
            self.assertIn("Report generated successfully", result)

    @patch('gql.Client.execute')
    def test_generate_crm_report_graphql_error(self, mock_execute):
        """Test report generation with GraphQL error"""
        # Mock GraphQL error
        mock_execute.side_effect = Exception("GraphQL connection failed")
        
        # Mock file operations
        mock_file = mock_open()
        with patch('builtins.open', mock_file):
            # Execute the task and expect it to raise the exception
            with self.assertRaises(Exception):
                generate_crm_report()
            
            # Verify error was logged
            handle = mock_file()
            written_content = ''.join(call[0][0] for call in handle.write.call_args_list)
            
            # Verify error log content
            self.assertRegex(
                written_content,
                r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} - Error generating report: GraphQL connection failed\n',
                "Error message should be logged"
            )

    def test_graphql_total_statistics(self):
        """Test GraphQL total statistics queries"""
        # Execute GraphQL query directly using the schema
        query = """
            query {
                totalCustomers
                totalOrders
                totalRevenue
            }
        """
        result = schema.execute(query)
        
        # Verify no errors
        self.assertIsNone(result.errors)
        
        # Verify data
        data = result.data
        self.assertEqual(data['totalCustomers'], 1)
        self.assertEqual(data['totalOrders'], 1)
        self.assertEqual(float(data['totalRevenue']), 20.00)

    @patch('gql.Client.execute')
    def test_report_file_creation(self, mock_execute):
        """Test actual file creation and content"""
        # Mock GraphQL response
        mock_execute.return_value = {
            'totalCustomers': 1,
            'totalOrders': 1,
            'totalRevenue': 20.00
        }
        
        log_file = '/tmp/crm_report_log.txt'
        
        # Remove existing log file if it exists
        if os.path.exists(log_file):
            os.remove(log_file)
        
        # Execute the task
        generate_crm_report()
        
        # Verify file was created
        self.assertTrue(os.path.exists(log_file))
        
        # Read and verify content
        with open(log_file, 'r') as f:
            content = f.read()
            
        self.assertRegex(
            content,
            r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} - Report: 1 customers, 1 orders, \$20.00 revenue\n',
            "Log file should contain correct report format"
        ) 