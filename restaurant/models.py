from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        
    def get_dishes(self):
        return self.dishes.all()
    
    def get_available_dishes(self):
        return self.dishes.filter(is_available=True)
    
    def get_all_dishes_in_category(self, available_only=True):
        if available_only:
            return self.dishes.filter(is_available=True)
        return self.dishes.all()
    
class Dish(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    categories = models.ManyToManyField(Category, related_name='dishes')
    image = models.ImageField(upload_to='dish_images/', blank=True, null=True)
    ingredients = models.CharField(max_length=255, blank=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Dish"
        verbose_name_plural = "Dishes"
        
    
    def is_available_for_order(self):
        return self.is_available
    
    def toggle_availability(self):
        self.is_available = not self.is_available
        self.save()
    
    def get_category_names(self):
        return ", ".join([category.name for category in self.categories.all()])
    
class Table(models.Model):
    table_num = models.PositiveIntegerField(unique=True)
    device_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    is_active = models.BooleanField(default=True)
    capacity = models.PositiveIntegerField(default=4)

    class Meta:
        verbose_name = "Table"
        verbose_name_plural = "Tables"
        
    def __str__(self):
        return f"Table {self.table_num}"
    
    def clean(self):
        if self.table_num <= 0:
            raise ValidationError("Table number must be positive")
         
    
    def get_active_orders(self):
        return Order.objects.filter(
            table=self, 
            status__in=[
                Order.OrderStatus.PENDING, 
                Order.OrderStatus.IN_PROGRESS, 
                Order.OrderStatus.READY
            ]
        )
    
    def get_completed_orders(self):
        return Order.objects.filter(
            table=self,
            status__in=[
                Order.OrderStatus.SERVED, 
                Order.OrderStatus.CANCELLED
            ]
        )
    
    def get_order_count(self):
        return self.orders.count()
    
    def get_total_revenue(self):
        total_revenue = self.orders.aggregate(total=models.Sum('total_price'))['total']
        return total_revenue if total_revenue else 0
    
    def get_last_order_time(self):
        last_order = self.orders.order_by('-order_time').first()
        return last_order.order_time if last_order else None

    def get_total_items(self):
        total_items = self.orders.aggregate(total=models.Sum('items_count'))['total']
        return total_items if total_items else 0
    
    
    def update_device(self, device_id):
        self.device_id = device_id
        self.save()
    
    @property
    def is_available(self):
        return self.get_active_orders().count() == 0
    
    
class Order(models.Model):
    class OrderStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        IN_PROGRESS = 'in_progress', 'In Progress'
        READY = 'ready', 'Ready'
        SERVED = 'served', 'Served'
        CANCELLED = 'cancelled', 'Cancelled'
        
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='orders')
    order_time = models.DateTimeField(auto_now_add=True)
    completed_time = models.DateTimeField(null=True, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  
    items_count = models.IntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=20, 
        choices=OrderStatus.choices, 
        default='pending'
    )
    
    prepared_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='prepared_orders',
        help_text="The chef who prepared this order"
    )
    served_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='served_orders',
        help_text="The waiter who served this order"
    )
    
    def __str__(self):
        return f"Order #{self.id} - {self.table}"
    
    def update_total_price(self):
        total = sum(item.price * item.quantity for item in self.items.all())  
        self.total_price = total
        self.items_count = sum(item.quantity for item in self.items.all())  
        self.save()
    
    def mark_as_in_progress(self, chef):
        """Chef marks order as being prepared"""
        if not chef or chef.role != 'chef':
            raise ValidationError("Only chefs can mark orders as in progress")
            
        old_status = self.status
        self.status = self.OrderStatus.IN_PROGRESS
        self.prepared_by = chef
        self.save()
        

    def mark_as_ready(self, chef):
        """Chef marks order as ready to be served"""
        if not chef or chef.role != 'chef':
            raise ValidationError("Only chefs can mark orders as ready")
            
        if self.status != self.OrderStatus.IN_PROGRESS:
            raise ValidationError("Order must be in progress before being marked as ready")
            
        old_status = self.status
        self.status = self.OrderStatus.READY
        self.save()

    def mark_as_served(self, waiter):
        """Waiter marks order as served to the table"""
        if not waiter or waiter.role != 'waiter':
            raise ValidationError("Only waiters can mark orders as served")
            
        if self.status != self.OrderStatus.READY:
            raise ValidationError("Order must be ready before being marked as served")
            
        old_status = self.status
        self.status = self.OrderStatus.SERVED
        self.served_by = waiter
        self.completed_time = timezone.now()
        self.save()

    def cancel_order(self, user):
        """Cancel an order - can be done by waiter or chef depending on status"""
        if self.status in [self.OrderStatus.SERVED, self.OrderStatus.CANCELLED]:
            raise ValidationError("Cannot cancel an order that is already served or cancelled")
            
        old_status = self.status
        self.status = self.OrderStatus.CANCELLED
        self.completed_time = timezone.now()
        self.save()
        
    def get_order_duration(self):
        if self.completed_time:
            return self.completed_time - self.order_time
        return timezone.now() - self.order_time
    
    @property
    def is_active(self):
        return self.status in [
            self.OrderStatus.PENDING, 
            self.OrderStatus.IN_PROGRESS, 
            self.OrderStatus.READY
        ]
    
    def can_be_modified_by_waiter(self):
        """Check if order can still be modified by waiter"""
        return self.status == self.OrderStatus.PENDING
    
    def can_be_modified_by_chef(self):
        """Check if order can be modified by chef"""
        return self.status in [self.OrderStatus.PENDING, self.OrderStatus.IN_PROGRESS]
    
    def get_allowed_next_statuses(self, user):
        """Get allowed next statuses based on current status and user role"""
        if user.role == 'waiter':
            if self.status == self.OrderStatus.PENDING:
                return [self.OrderStatus.CANCELLED]
            elif self.status == self.OrderStatus.READY:
                return [self.OrderStatus.SERVED, self.OrderStatus.CANCELLED]
            else:
                return []
        elif user.role == 'chef':
            if self.status == self.OrderStatus.PENDING:
                return [self.OrderStatus.IN_PROGRESS, self.OrderStatus.CANCELLED]
            elif self.status == self.OrderStatus.IN_PROGRESS:
                return [self.OrderStatus.READY, self.OrderStatus.CANCELLED]
            else:
                return []
        elif user.role == 'admin':
            # Admins can change to any status
            return [status[0] for status in self.OrderStatus.choices]
        else:
            return []
        

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.dish.name}"
    
    def get_total_price(self):
        return self.quantity * self.price
    
    def get_dish_name(self):
        return self.dish.name
    
    def save(self, *args, **kwargs):
        # Automatically set price from the dish if not specified
        if self.price is None:
            self.price = self.dish.price
        super().save(*args, **kwargs)
        
        self.order.update_total_price()
        
    def clean(self):
        if self.quantity < 1:
            raise ValidationError("Quantity must be at least 1")

        
class Stats(models.Model):
    date = models.DateField(unique=True)
    total_orders = models.IntegerField(default=0)  
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)  
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Total revenue for the day/week/month
    peak_hour = models.IntegerField(null=True, blank=True)  # Hour with the highest number of orders (24-hour format)
    items_sold = models.IntegerField(default=0)  # Total items sold

    def __str__(self):
        return f"Stats for {self.date}"

    @classmethod
    def generate_for_date(cls, date):
        """Generate statistics for a specific date"""
        # Get orders for the specific date
        daily_orders = Order.objects.filter(
            order_time__date=date,
            status__in=[Order.OrderStatus.SERVED, Order.OrderStatus.CANCELLED]
        )
        
        # Calculate statistics
        total_orders = daily_orders.count()
        
        if total_orders == 0:
            return cls.objects.update_or_create(
                date=date,
                defaults={
                    'total_orders': 0,
                    'total_revenue': 0,
                    'items_sold': 0,
                    'average_order_value': 0,
                    'peak_hour': None,
                }
            )[0]  # Return the actual object, not the tuple
        
        total_revenue = daily_orders.aggregate(total=models.Sum('total_price'))['total'] or 0
        items_sold = daily_orders.aggregate(total=models.Sum('items_count'))['total'] or 0
        avg_order = total_revenue / total_orders if total_orders > 0 else 0
        
        # Find peak hour
        hour_counts = {}
        for order in daily_orders:
            hour = order.order_time.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        peak_hour = max(hour_counts.items(), key=lambda x: x[1])[0] if hour_counts else None
        
        # Create or update stats object
        stats, created = cls.objects.update_or_create(
            date=date,
            defaults={
                'total_orders': total_orders,
                'total_revenue': total_revenue,
                'items_sold': items_sold,
                'average_order_value': avg_order,
                'peak_hour': peak_hour,
            }
        )
        return stats

    @classmethod
    def get_stats_for_date_range(cls, start_date, end_date):
        return cls.objects.filter(date__range=[start_date, end_date])
    
    @classmethod 
    def get_monthly_stats(cls, year, month):
        """Get aggregated statistics for a specific month"""
        monthly_stats = cls.objects.filter(date__year=year, date__month=month)
        
        # Aggregate monthly totals
        aggregated = monthly_stats.aggregate(
            total_orders=models.Sum('total_orders'),
            total_revenue=models.Sum('total_revenue'),
            items_sold=models.Sum('items_sold'),
        )
        
        # Calculate average
        avg_order = (aggregated['total_revenue'] / aggregated['total_orders'] 
                    if aggregated['total_orders'] else 0)
        
        return {
            'total_orders': aggregated['total_orders'] or 0,
            'total_revenue': aggregated['total_revenue'] or 0,
            'items_sold': aggregated['items_sold'] or 0,
            'average_order_value': avg_order,
            'period': f"{year}-{month}"
        }
    