# restaurant/serializers.py
from rest_framework import serializers
from .models import Category, Dish, Table, Order, OrderItem, Stats, Ingredient
from users.models import User
import uuid

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'image']
        read_only_fields = ['id']

class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'icon']


class DishSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    ingredients = ingredients = IngredientSerializer(many=True)

    class Meta:
        model = Dish
        fields = ['id', 'name', 'description', 'price', 'categories', 
                 'image', 'ingredients', 'time', 'is_available']
        read_only_fields = ['id']
        
    def validate(self, value):
        """Validate that the dish is available"""
        if value.get("is_available") is False:
            raise serializers.ValidationError(f"The dish '{value.get('name', 'Unknown')}' is not available")
        return value


        
class TableSerializer(serializers.ModelSerializer):
    is_available = serializers.BooleanField(read_only=True)
    active_orders_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Table
        fields = ['id', 'table_num', 'device_id', 'is_active', 'capacity', 
                 'is_available', 'active_orders_count']
        read_only_fields = ['id', 'device_id', 'is_available', 'active_orders_count']
        
class TableLinkSerializer(serializers.Serializer):
    table_num = serializers.IntegerField()

    def validate(self, data):
        table_num = data.get('table_num')

        try:
            table = Table.objects.get(table_num=table_num)

            if table.device_id:
                raise serializers.ValidationError(
                    "This table is already linked to a device. Please reset it from the admin panel."
                )
        except Table.DoesNotExist:
            raise serializers.ValidationError("Table does not exist")

        return data

    def save(self):
        table_num = self.validated_data.get('table_num')

        table = Table.objects.get(table_num=table_num)
        generated_uuid = uuid.uuid4()  # Backend generates the device_id

        table.device_id = generated_uuid
        table.save()

        return table
    
    
class OrderItemSerializer(serializers.ModelSerializer):
    dish_name = serializers.CharField(source='dish.name', read_only=True)
    total_price = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'dish', 'dish_name', 'quantity', 'price', 'total_price']
        read_only_fields = ['id', 'total_price']
        

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    table_number = serializers.IntegerField(source='table.table_num', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration = serializers.DurationField(source='get_order_duration', read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'table', 'table_number', 'order_time', 'completed_time',
                 'total_price', 'items_count', 'status', 'status_display',
                 'prepared_by', 'served_by', 'items', 'duration']
        read_only_fields = ['id', 'order_time', 'completed_time', 'total_price',
                          'items_count', 'status_display', 'duration']
        extra_kwargs = {
            'table': {'write_only': True}
        }

class StatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stats
        fields = ['date', 'total_orders', 'average_order_value', 
                 'total_revenue', 'peak_hour', 'items_sold']