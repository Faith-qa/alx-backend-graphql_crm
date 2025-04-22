from django.test import TestCase
from graphene.test import Client
from .schema import schema

class HelloQueryTests(TestCase):
    def setUp(self):
        self.client = Client(schema)

    def test_hello_query(self):
        """Test that the hello query returns the expected response"""
        query = '''
            query {
                hello
            }
        '''
        result = self.client.execute(query)
        self.assertIn('data', result)
        self.assertEqual(result['data']['hello'], "Hello, GraphQL!")

    def test_hello_query_with_operation_name(self):
        """Test that the hello query works with operation name"""
        query = '''
            query TestQuery {
                hello
            }
        '''
        result = self.client.execute(query, operation_name='TestQuery')
        self.assertIn('data', result)
        self.assertEqual(result['data']['hello'], "Hello, GraphQL!") 