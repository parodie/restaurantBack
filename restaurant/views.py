from rest_framework import viewsets, generics
from restaurant.models import *
from restaurant.serializers import *
from users.permissions import *
from django.core.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

#Admin's views 
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdmin]

class DishAdminViewSet(viewsets.ModelViewSet):
    queryset = Dish.objects.all()
    serializer_class = DishSerializer
    permission_classes = [IsAdmin]

class TableAdminViewSet(viewsets.ModelViewSet):
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    permission_classes = [IsAdmin]

class StatsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Stats.objects.all()
    serializer_class = StatsSerializer
    permission_classes = [IsAdmin]
    
    
#chef's views or actions
class ChefOrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsChef]

    @action(detail=True, methods=['post'])
    def mark_as_in_progress(self, request, pk=None):
        order = self.get_object()
        try:
            order.mark_as_in_progress(request.user)
            return Response({'status': 'Order in progress'})
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=True, methods=['post'])
    def mark_as_ready(self, request, pk=None):
        order = self.get_object()
        try:
            order.mark_as_ready(request.user)
            return Response({'status': 'Order ready'})
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        try:
            order.cancel_order(request.user)
            return Response({'status': 'Order cancelled'})
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)
  
#waiter views or actions      
class WaiterOrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsWaiter]

    @action(detail=True, methods=['post'])
    def mark_as_served(self, request, pk=None):
        order = self.get_object()
        try:
            order.mark_as_served(request.user)
            return Response({'status': 'Order served'})
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)
        
class ClientCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsTableDevice]

    @action(detail=True, methods=['get'])
    def dishes(self, request, pk=None):
        category = self.get_object()
        serializer = DishSerializer(category.get_available_dishes(), many=True)
        return Response(serializer.data)

class ClientDishViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DishSerializer
    permission_classes = [IsTableDevice]

    def get_queryset(self):
        return Dish.objects.filter(is_available=True)

    @action(detail=False, methods=['get'])
    def search(self, request):
        q = request.query_params.get('q')
        if not q:
            return Response({"error": "Query param 'q' is required"}, status=400)
        dishes = Dish.objects.filter(name__icontains=q, is_available=True)
        return Response(DishSerializer(dishes, many=True).data)

class ClientOrderView(generics.CreateAPIView, generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsTableDevice]

    def get_queryset(self):
        return Order.objects.filter(table=self.request.table).exclude(status=Order.OrderStatus.SERVED)

    def create(self, request, *args, **kwargs):
        items_data = request.data.get('items', [])
        if not items_data:
            return Response({"error": "Order must contain items"}, status=400)

        order = Order.objects.create(table=request.table, status=Order.OrderStatus.PENDING)

        for item in items_data:
            dish_id = item.get('dish')
            quantity = item.get('quantity', 1)
            try:
                dish = Dish.objects.get(id=dish_id, is_available=True)
                OrderItem.objects.create(order=order, dish=dish, quantity=quantity, price=dish.price)
            except Dish.DoesNotExist:
                order.delete()
                return Response({"error": f"Dish {dish_id} not available"}, status=400)

        order.update_total_price()
        return Response({
            "message": "Order placed",
            "order_id": order.id,
            "status": order.status,
            "total_price": str(order.total_price)
        }, status=201)
