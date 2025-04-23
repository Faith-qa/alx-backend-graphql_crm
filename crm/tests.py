from django.test import TestCase
from graphene.test import Client
from decimal import Decimal
from .models import Customer, Product, Order
from .schema import schema
from django.utils import timezone
import json
from django.utils import timezone
from datetime import datetime, timedelta
from graphene_django.utils.testing import GraphQLTestCase

class GraphQLCRMTestCase(TestCase):
    def setUp(self):
        self.client = Client(schema)
        # Create test data
        self.customer = Customer.objects.create(
            name="Test User",
            email="test@example.com",
            phone="+1234567890"
        )
        self.product = Product.objects.create(
            name="Test Product",
            price=Decimal("99.99"),
            stock=10
        )

    def test_create_customer_success(self):
        """Test creating a customer with valid data"""
        query = '''
        mutation {
            createCustomer(input: {
                name: "John Doe",
                email: "john@example.com",
                phone: "+1987654321"
            }) {
                customer {
                    id
                    name
                    email
                    phone
                }
                message
            }
        }
        '''
        response = self.client.execute(query)
        self.assertIsNone(response.get('errors'))
        self.assertEqual(response['data']['createCustomer']['customer']['name'], "John Doe")
        self.assertEqual(response['data']['createCustomer']['message'], "Customer created successfully")

    def test_create_customer_duplicate_email(self):
        """Test creating a customer with duplicate email"""
        query = '''
        mutation {
            createCustomer(input: {
                name: "Another User",
                email: "test@example.com",
                phone: "+1987654321"
            }) {
                customer {
                    id
                }
                message
            }
        }
        '''
        response = self.client.execute(query)
        self.assertIsNotNone(response.get('errors'))
        self.assertIn('Email already exists', str(response['errors']))

    def test_create_customer_invalid_phone(self):
        """Test creating a customer with invalid phone number"""
        query = '''
        mutation {
            createCustomer(input: {
                name: "Invalid Phone",
                email: "invalid@example.com",
                phone: "123"
            }) {
                customer {
                    id
                }
                message
            }
        }
        '''
        response = self.client.execute(query)
        self.assertIsNotNone(response.get('errors'))
        self.assertIn('Invalid phone number format', str(response['errors']))

    def test_bulk_create_customers_success(self):
        """Test bulk creation of customers with valid data"""
        query = '''
        mutation {
            bulkCreateCustomers(input: [
                {name: "Bulk1", email: "bulk1@example.com", phone: "+1111111111"},
                {name: "Bulk2", email: "bulk2@example.com", phone: "123-456-7890"}
            ]) {
                customers {
                    id
                    name
                    email
                }
                errors
            }
        }
        '''
        response = self.client.execute(query)
        self.assertIsNone(response.get('errors'))
        self.assertEqual(len(response['data']['bulkCreateCustomers']['customers']), 2)
        self.assertEqual(len(response['data']['bulkCreateCustomers']['errors']), 0)

    def test_bulk_create_customers_partial_success(self):
        """Test bulk creation with some invalid customers"""
        query = '''
        mutation {
            bulkCreateCustomers(input: [
                {name: "Valid", email: "valid@example.com", phone: "+1111111111"},
                {name: "Invalid", email: "test@example.com", phone: "123-456-7890"},
                {name: "Another", email: "another@example.com", phone: "invalid"}
            ]) {
                customers {
                    id
                    name
                    email
                }
                errors
            }
        }
        '''
        response = self.client.execute(query)
        self.assertIsNone(response.get('errors'))
        customers = response['data']['bulkCreateCustomers']['customers']
        errors = response['data']['bulkCreateCustomers']['errors']
        self.assertEqual(len(customers), 1)  # Only one valid customer
        self.assertEqual(len(errors), 2)     # Two errors for invalid customers

    def test_create_product_success(self):
        """Test creating a product with valid data"""
        query = '''
        mutation {
            createProduct(input: {
                name: "New Product",
                price: 199.99,
                stock: 5
            }) {
                product {
                    id
                    name
                    price
                    stock
                }
            }
        }
        '''
        response = self.client.execute(query)
        self.assertIsNone(response.get('errors'))
        self.assertEqual(response['data']['createProduct']['product']['name'], "New Product")
        self.assertEqual(response['data']['createProduct']['product']['price'], "199.99")

    def test_create_product_negative_price(self):
        """Test creating a product with negative price"""
        query = '''
        mutation {
            createProduct(input: {
                name: "Negative Price",
                price: -10.00,
                stock: 5
            }) {
                product {
                    id
                }
            }
        }
        '''
        response = self.client.execute(query)
        self.assertIsNotNone(response.get('errors'))
        self.assertIn('Price must be positive', str(response['errors']))

    def test_create_product_negative_stock(self):
        """Test creating a product with negative stock"""
        query = '''
        mutation {
            createProduct(input: {
                name: "Negative Stock",
                price: 10.00,
                stock: -5
            }) {
                product {
                    id
                }
            }
        }
        '''
        response = self.client.execute(query)
        self.assertIsNotNone(response.get('errors'))
        self.assertIn('Stock cannot be negative', str(response['errors']))

    def test_create_order_success(self):
        """Test creating an order with valid data"""
        product2 = Product.objects.create(
            name="Second Product",
            price=Decimal("50.00"),
            stock=5
        )
        query = f'''
        mutation {{
            createOrder(input: {{
                customerId: "{self.customer.id}",
                productIds: ["{self.product.id}", "{product2.id}"]
            }}) {{
                order {{
                    id
                    customer {{
                        name
                    }}
                    products {{
                        id
                        name
                    }}
                    totalAmount
                }}
                message
            }}
        }}
        '''
        response = self.client.execute(query)
        self.assertIsNone(response.get('errors'))
        self.assertEqual(response['data']['createOrder']['message'], "Order created successfully")
        self.assertEqual(response['data']['createOrder']['order']['totalAmount'], "149.99")

    def test_create_order_invalid_customer(self):
        """Test creating an order with invalid customer ID"""
        query = '''
        mutation {
            createOrder(input: {
                customerId: "999",
                productIds: ["1"]
            }) {
                order {
                    id
                }
                message
            }
        }
        '''
        response = self.client.execute(query)
        self.assertIsNotNone(response.get('errors'))
        self.assertIn('Customer not found', str(response['errors']))

    def test_create_order_invalid_products(self):
        """Test creating an order with invalid product IDs"""
        query = f'''
        mutation {{
            createOrder(input: {{
                customerId: "{self.customer.id}",
                productIds: ["999", "888"]
            }}) {{
                order {{
                    id
                }}
                message
            }}
        }}
        '''
        response = self.client.execute(query)
        self.assertIsNotNone(response.get('errors'))
        self.assertIn('Products not found', str(response['errors']))

    def test_create_order_no_products(self):
        """Test creating an order without products"""
        query = f'''
        mutation {{
            createOrder(input: {{
                customerId: "{self.customer.id}",
                productIds: []
            }}) {{
                order {{
                    id
                }}
                message
            }}
        }}
        '''
        response = self.client.execute(query)
        self.assertIsNotNone(response.get('errors'))
        self.assertIn('At least one product is required', str(response['errors']))

    def test_query_customers(self):
        """Test querying all customers"""
        query = '''
        query {
            allCustomers {
                id
                name
                email
                phone
            }
        }
        '''
        response = self.client.execute(query)
        self.assertIsNone(response.get('errors'))
        self.assertTrue(len(response['data']['allCustomers']) > 0)

    def test_query_single_customer(self):
        """Test querying a single customer by ID"""
        query = f'''
        query {{
            customer(id: "{self.customer.id}") {{
                id
                name
                email
                phone
            }}
        }}
        '''
        response = self.client.execute(query)
        self.assertIsNone(response.get('errors'))
        self.assertEqual(response['data']['customer']['email'], "test@example.com")

    def test_query_products(self):
        """Test querying all products"""
        query = '''
        query {
            allProducts {
                id
                name
                price
                stock
            }
        }
        '''
        response = self.client.execute(query)
        self.assertIsNone(response.get('errors'))
        self.assertTrue(len(response['data']['allProducts']) > 0)

    def test_query_orders(self):
        """Test querying all orders"""
        # First create an order
        order = Order.objects.create(
            customer=self.customer,
            total_amount=self.product.price
        )
        order.products.add(self.product)

        query = '''
        query {
            allOrders {
                id
                totalAmount
                customer {
                    name
                }
                products {
                    id
                    name
                }
            }
        }
        '''
        response = self.client.execute(query)
        self.assertIsNone(response.get('errors'))
        self.assertTrue(len(response['data']['allOrders']) > 0)

class CRMFilterTests(GraphQLTestCase):
    GRAPHQL_URL = '/graphql/'

    def setUp(self):
        # Create test customers
        self.customer1 = Customer.objects.create(
            name="John Doe",
            email="john@example.com",
            phone="+1234567890"
        )
        self.customer2 = Customer.objects.create(
            name="Jane Smith",
            email="jane@example.com",
            phone="123-456-7890"
        )
        self.customer3 = Customer.objects.create(
            name="Bob Johnson",
            email="bob@example.com",
            phone="+1987654321"
        )

        # Create test products
        self.product1 = Product.objects.create(
            name="Laptop",
            price=Decimal('999.99'),
            stock=10
        )
        self.product2 = Product.objects.create(
            name="Smartphone",
            price=Decimal('499.99'),
            stock=20
        )
        self.product3 = Product.objects.create(
            name="Tablet",
            price=Decimal('299.99'),
            stock=5
        )

        # Create test orders
        self.order1 = Order.objects.create(
            customer=self.customer1,
            total_amount=Decimal('1499.98'),
            order_date=timezone.now()
        )
        self.order1.products.add(self.product1, self.product2)

        self.order2 = Order.objects.create(
            customer=self.customer2,
            total_amount=Decimal('799.98'),
            order_date=timezone.now() - timedelta(days=1)
        )
        self.order2.products.add(self.product2, self.product3)

    def test_filter_customers_by_name(self):
        query = '''
        query {
            allCustomers(name: "John Doe") {
                id
                name
                email
                phone
            }
        }
        '''
        response = self.query(query)
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)
        customers = content['data']['allCustomers']
        self.assertEqual(len(customers), 1)
        self.assertEqual(customers[0]['name'], "John Doe")

    def test_filter_customers_by_email(self):
        query = '''
        query {
            allCustomers(email: "jane") {
                id
                name
                email
            }
        }
        '''
        response = self.query(query)
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)
        customers = content['data']['allCustomers']
        self.assertEqual(len(customers), 1)
        self.assertEqual(customers[0]['email'], "jane@example.com")

    def test_filter_customers_by_phone(self):
        query = '''
        query {
            allCustomers(phonePattern: "+1") {
                id
                name
                phone
            }
        }
        '''
        response = self.query(query)
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)
        customers = content['data']['allCustomers']
        self.assertEqual(len(customers), 2)  # John and Bob have +1 numbers

    def test_filter_products_by_price_range(self):
        query = '''
        query {
            allProducts(priceGte: 400, priceLte: 600) {
                id
                name
                price
            }
        }
        '''
        response = self.query(query)
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)
        products = content['data']['allProducts']
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0]['name'], "Smartphone")

    def test_filter_products_by_stock(self):
        query = '''
        query {
            allProducts(stockGte: 10) {
                id
                name
                stock
            }
        }
        '''
        response = self.query(query)
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)
        products = content['data']['allProducts']
        self.assertEqual(len(products), 2)  # Laptop and Smartphone

    def test_filter_orders_by_total_amount(self):
        query = '''
        query {
            allOrders(totalAmountGte: 1000) {
                id
                totalAmount
                customer {
                    name
                }
            }
        }
        '''
        response = self.query(query)
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)
        orders = content['data']['allOrders']
        self.assertEqual(len(orders), 1)  # Only order1 has total_amount >= 1000

    def test_filter_orders_by_customer_name(self):
        query = '''
        query {
            allOrders(customerName: "Jane") {
                id
                customer {
                    name
                }
            }
        }
        '''
        response = self.query(query)
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)
        orders = content['data']['allOrders']
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]['customer']['name'], "Jane Smith")

    def test_filter_orders_by_product(self):
        query = f'''
        query {{
            allOrders(productId: "{self.product2.id}") {{
                id
                products {{
                    id
                    name
                }}
            }}
        }}
        '''
        response = self.query(query)
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)
        orders = content['data']['allOrders']
        self.assertEqual(len(orders), 2)  # Both orders contain product2

    def test_query_customers(self):
        """Test querying all customers"""
        query = '''
        query {
            allCustomers {
                id
                name
                email
                phone
            }
        }
        '''
        response = self.query(query)
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)
        customers = content['data']['allCustomers']
        self.assertEqual(len(customers), 3)  # We created 3 customers in setUp

    def test_query_products(self):
        """Test querying all products"""
        query = '''
        query {
            allProducts {
                id
                name
                price
                stock
            }
        }
        '''
        response = self.query(query)
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)
        products = content['data']['allProducts']
        self.assertEqual(len(products), 3)  # We created 3 products in setUp

    def test_query_orders(self):
        """Test querying all orders"""
        query = '''
        query {
            allOrders {
                id
                totalAmount
                customer {
                    name
                }
                products {
                    id
                    name
                }
            }
        }
        '''
        response = self.query(query)
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)
        orders = content['data']['allOrders']
        self.assertEqual(len(orders), 2)  # We created 2 orders in setUp
