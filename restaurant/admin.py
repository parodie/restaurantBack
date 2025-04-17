from django.contrib import admin
from .models import Category, Dish, Table, Order, OrderItem, Stats, Ingredient

### Editable Models ###

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')

@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'is_available']
    list_filter = ['is_available']
    search_fields = ['name']
    filter_horizontal = ("categories", "ingredients")


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ['table_num', 'capacity', 'is_active', 'device_id']
    list_filter = ['is_active', ]
    search_fields = ['table_num', 'device_id']

### Read-only Models ###

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'table', 'status', 'order_time', 'completed_time', 'total_price']
    list_filter = ['status', 'order_time']
    search_fields = ['table__table_num']
    readonly_fields = ['table', 'status', 'order_time', 'completed_time', 
                       'total_price', 'items_count', 'prepared_by', 'served_by']
    inlines = []  # No OrderItemInline
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['dish', 'quantity', 'price']
    readonly_fields = ['dish', 'quantity', 'price', 'order']
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False


@admin.register(Stats)
class StatsAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_orders', 'total_revenue', 'average_order_value', 'peak_hour']
    readonly_fields = [field.name for field in Stats._meta.fields]
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
