from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Order, Table, Dish, Category

User = get_user_model()

class OrderStatusTests(TestCase):
    def setUp(self):
        # Create test data
        self.chef = User.objects.create_user(
            username='chef1', 
            password='testpass', 
            password2='testpass', 
            role='chef'
        )
        self.waiter = User.objects.create_user(
            username='waiter1', 
            password='testpass', 
            password2='testpass', 
            role='waiter'
        )
        self.table = Table.objects.create(table_num=1, capacity=4)
        self.category = Category.objects.create(name='Main Course')
        self.dish = Dish.objects.create(
            name='Pasta', 
            price=12.99,
            is_available=True
        )
        self.dish.categories.add(self.category)
        
    def test_valid_status_transitions(self):
        """Test valid order status transitions"""
        order = Order.objects.create(
            table=self.table,
            total_price=0,
            items_count=0,
            status=Order.OrderStatus.PENDING
        )
        
        # Chef marks as in progress
        order.mark_as_in_progress(self.chef)
        self.assertEqual(order.status, Order.OrderStatus.IN_PROGRESS)
        self.assertEqual(order.prepared_by, self.chef)
        
        # Chef marks as ready
        order.mark_as_ready(self.chef)
        self.assertEqual(order.status, Order.OrderStatus.READY)
        
        # Waiter marks as served
        order.mark_as_served(self.waiter)
        self.assertEqual(order.status, Order.OrderStatus.SERVED)
        self.assertEqual(order.served_by, self.waiter)
    
    def test_invalid_transitions(self):
        """Test invalid status transitions raise errors"""
        order = Order.objects.create(
            table=self.table,
            total_price=0,
            items_count=0,
            status=Order.OrderStatus.PENDING
        )
        
        # Waiter can't mark as in progress
        with self.assertRaises(ValidationError):
            order.mark_as_in_progress(self.waiter)
            
        # Chef can't mark as served
        order.mark_as_in_progress(self.chef)
        with self.assertRaises(ValidationError):
            order.mark_as_served(self.chef)
    
    def test_cancel_order(self):
        """Test order cancellation scenarios"""
        order = Order.objects.create(
            table=self.table,
            total_price=0,
            items_count=0,
            status=Order.OrderStatus.PENDING
        )
        
        # Waiter can cancel pending order
        order.cancel_order(self.waiter)
        self.assertEqual(order.status, Order.OrderStatus.CANCELLED)
        
        # Can't cancel already cancelled order
        with self.assertRaises(ValidationError):
            order.cancel_order(self.waiter)