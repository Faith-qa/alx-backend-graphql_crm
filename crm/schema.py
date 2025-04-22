import graphene
from graphene_django import DjangoObjectType
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Customer, Product, Order
import re
from decimal import Decimal

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ('id', 'name', 'email', 'phone', 'created_at', 'orders')

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ('id', 'name', 'price', 'stock', 'created_at', 'orders')

    def resolve_price(self, info):
        return str(self.price)

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ('id', 'customer', 'products', 'total_amount', 'order_date', 'created_at')

    def resolve_total_amount(self, info):
        return str(self.total_amount)

class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)

class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Float(required=True)
    stock = graphene.Int(required=False, default_value=0)

class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime(required=False)

class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    @staticmethod
    def validate_phone(phone):
        if not phone:
            return True
        pattern = r'^\+?1?\d{9,15}$|^\d{3}-\d{3}-\d{4}$'
        return bool(re.match(pattern, phone))

    def mutate(root, info, input):
        if not CreateCustomer.validate_phone(input.phone):
            raise ValidationError("Invalid phone number format")

        try:
            # Check for duplicate email
            if Customer.objects.filter(email=input.email).exists():
                raise ValidationError("Email already exists")

            customer = Customer.objects.create(
                name=input.name,
                email=input.email,
                phone=input.phone
            )
            return CreateCustomer(
                customer=customer,
                message="Customer created successfully"
            )
        except ValidationError as e:
            raise ValidationError(str(e))
        except Exception as e:
            raise ValidationError(f"Error creating customer: {str(e)}")

class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    def mutate(root, info, input):
        customers = []
        errors = []

        with transaction.atomic():
            for customer_data in input:
                try:
                    if not CreateCustomer.validate_phone(customer_data.phone):
                        errors.append(f"Invalid phone number for {customer_data.name}")
                        continue

                    customer = Customer.objects.create(
                        name=customer_data.name,
                        email=customer_data.email,
                        phone=customer_data.phone
                    )
                    customers.append(customer)
                except Exception as e:
                    errors.append(f"Error creating customer {customer_data.name}: {str(e)}")

        return BulkCreateCustomers(customers=customers, errors=errors)

class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)

    def mutate(root, info, input):
        if input.price <= 0:
            raise ValidationError("Price must be positive")
        if input.stock < 0:
            raise ValidationError("Stock cannot be negative")

        try:
            product = Product.objects.create(
                name=input.name,
                price=Decimal(str(input.price)),
                stock=input.stock
            )
            return CreateProduct(product=product)
        except ValidationError as e:
            raise ValidationError(str(e))

class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderType)
    message = graphene.String()

    def mutate(root, info, input):
        try:
            # Validate customer exists
            try:
                customer = Customer.objects.get(pk=input.customer_id)
            except Customer.DoesNotExist:
                raise ValidationError("Customer not found")

            # Validate products exist and are valid
            if not input.product_ids:
                raise ValidationError("At least one product is required")

            products = Product.objects.filter(id__in=input.product_ids)
            if len(products) != len(input.product_ids):
                missing_products = set(input.product_ids) - set(str(p.id) for p in products)
                raise ValidationError(f"Products not found: {', '.join(missing_products)}")

            # Create order with atomic transaction
            with transaction.atomic():
                order = Order.objects.create(
                    customer=customer,
                    total_amount=Decimal('0'),
                    order_date=input.order_date if input.order_date else None
                )
                order.products.set(products)
                
                # Calculate total amount as sum of product prices
                total = sum(product.price for product in products)
                order.total_amount = total
                order.save()

            return CreateOrder(
                order=order,
                message="Order created successfully"
            )
        except ValidationError as e:
            raise ValidationError(str(e))
        except Exception as e:
            raise ValidationError(f"Error creating order: {str(e)}")

class Query(graphene.ObjectType):
    customers = graphene.List(CustomerType)
    products = graphene.List(ProductType)
    orders = graphene.List(OrderType)
    customer = graphene.Field(CustomerType, id=graphene.ID())
    product = graphene.Field(ProductType, id=graphene.ID())
    order = graphene.Field(OrderType, id=graphene.ID())

    def resolve_customers(self, info):
        return Customer.objects.all()

    def resolve_products(self, info):
        return Product.objects.all()

    def resolve_orders(self, info):
        return Order.objects.all()

    def resolve_customer(self, info, id):
        try:
            return Customer.objects.get(pk=id)
        except Customer.DoesNotExist:
            return None

    def resolve_product(self, info, id):
        try:
            return Product.objects.get(pk=id)
        except Product.DoesNotExist:
            return None

    def resolve_order(self, info, id):
        try:
            return Order.objects.get(pk=id)
        except Order.DoesNotExist:
            return None

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()

schema = graphene.Schema(query=Query, mutation=Mutation) 