from rest_framework import viewsets, generics
from restaurant.models import *
from restaurant.serializers import *
from users.permissions import *
from django.core.exceptions import ValidationError
from rest_framework.decorators import action, api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.db import transaction
from restaurant.auth import DeviceJWTAuthentication


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
        
#client wiews or actions
class ClientCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    authentication_classes = [DeviceJWTAuthentication]
    permission_classes = [IsTableDevice]

    @action(detail=True, methods=['get'])
    def dishes(self, request, pk=None):
        category = self.get_object()
        serializer = DishSerializer(category.get_available_dishes(), many=True)
        return Response(serializer.data)

class ClientDishViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DishSerializer
    authentication_classes = [DeviceJWTAuthentication]
    permission_classes = [IsTableDevice]

    def get_queryset(self):
        queryset = Dish.objects.filter(is_available=True)
        
        categories = self.request.query_params.get('categories')

        if categories:
            category_list = categories.split(',')  
            queryset = queryset.filter(categories__name__in=category_list)

        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)
        if min_price and max_price:
            queryset = queryset.filter(price__gte=min_price, price__lte=max_price)
        elif min_price:
            queryset = queryset.filter(price__gte=min_price)
        elif max_price:
            queryset = queryset.filter(price__lte=max_price)

        return queryset

    @action(detail=False, methods=['get'])
    def search(self, request):
        q = request.query_params.get('q')
        if not q:
            return Response({"error": "Query param 'q' is required"}, status=400)
        dishes = Dish.objects.filter(name__icontains=q, is_available=True)
        return Response(DishSerializer(dishes, many=True).data)

class ClientOrderView(generics.CreateAPIView, generics.ListAPIView):
    serializer_class = OrderSerializer
    authentication_classes = [DeviceJWTAuthentication]
    permission_classes = [IsTableDevice] 

    def get_queryset(self):
        table = getattr(self.request, "table", None)
        if table:
            return Order.objects.filter(table=table).exclude(status=Order.OrderStatus.SERVED)
        return Order.objects.none()  

    def create(self, request, *args, **kwargs):
        #table_id = request.data.get('table') 
        #if not table_id:
        #    return Response({"error": "Table is required"}, status=400)

        table = getattr(request, "table", None) 
        if not table:
            return Response({"error": "Unauthorized"}, status=403)
            
        items_data = request.data.get('items', [])
        if not items_data:
            return Response({"error": "Order must contain items"}, status=400)

        with transaction.atomic():
            order = Order.objects.create(table=table, status=Order.OrderStatus.PENDING)

            for item in items_data:
                dish_id = item.get('dish')
                quantity = item.get('quantity', 1)

                try:
                    dish = Dish.objects.get(id=dish_id, is_available=True)
                    OrderItem.objects.create(order=order, dish=dish, quantity=quantity, price=dish.price)
                except Dish.DoesNotExist:
                    order.delete()  
                    raise ValidationError(f"Dish {dish_id} not available")

            order.update_total_price()

        return Response({
            "message": "created",
            "order_id": order.id,
            "status": order.status,
            "total_price": str(order.total_price)
        }, status=201)
        

class ClientOrderCancelView(APIView):
    authentication_classes = [DeviceJWTAuthentication]
    permission_classes = [IsTableDevice]

    def post(self, request, pk):
        try:
            order = Order.objects.get(pk=pk, table=request.table)
            
            if order.status != Order.OrderStatus.PENDING:
                return Response({"error": "Only pending orders can be cancelled."}, status=400)

            order.status = Order.OrderStatus.CANCELLED
            order.save()
            
            return Response({
                "status": "success",
                "message": "Order cancelled successfully",
                "order_id": order.id,
                "new_status": order.status
            })
            
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)
        
class ClientOrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    authentication_classes = [DeviceJWTAuthentication]
    permission_classes = [IsTableDevice]

    def get_queryset(self):
        table = getattr(self.request, "table", None)
        if table:
            return Order.objects.filter(
                table=table,
                expired=False 
            )
        return Order.objects.none()
    
    
class ClientExpireOrdersView(APIView):
    authentication_classes = [DeviceJWTAuthentication]
    permission_classes = [IsTableDevice]
    
    def post(self, request, *args, **kwargs):
        table = getattr(request, "table", None)
        if not table:
            return Response(
                {"error": "Table authentication required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Only expire served or cancelled orders
        expired_count = Order.objects.filter(
            table=table,
            expired=False,
            status__in=[Order.OrderStatus.SERVED, Order.OrderStatus.CANCELLED]
        ).update(expired=True)
        
        return Response({
            "message": f"Marked {expired_count} orders as expired",
            "expired_count": expired_count
        })
        
class ResetTableView(APIView):
    authentication_classes = [DeviceJWTAuthentication]
    permission_classes = [IsTableDevice]
    def post(self, request):
        table_num = request.table_num  

        try:
            table = Table.objects.get(table_num=table_num)
            table.device_id = None
            table.save()
            return Response({"message": "Device unlinked successfully."}, status=status.HTTP_200_OK)
        except Table.DoesNotExist:
            return Response({"error": "Table not found."}, status=status.HTTP_400_BAD_REQUEST)

        
#link view 
"""class LinkDeviceToTableView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        print("Received data:", request.data)
        serializer = TableLinkSerializer(data=request.data)
        if serializer.is_valid():
            table = serializer.save()
            return Response({
                "message": f"Device linked to Table {table.table_num}",
                "device_id": str(table.device_id),  
                "table_num": table.table_num
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)"""

class LinkDeviceToTableView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TableLinkSerializer(data=request.data)
        print("Received data:", request.data)
        serializer = TableLinkSerializer(data=request.data)
        
        if serializer.is_valid():
            table, token = serializer.save()

            return Response({
                "message": f"Device successfully linked to Table {table.table_num}",
                "token": token  
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([]) 
def verify_device(request):
    print("Inside verify_device") 
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return Response({"error": "Invalid Authorization header"}, status=400)
    
    token = auth_header.split(' ')[1]
    table_num = request.data.get('table_num')
    
    if not table_num:
        return Response({"error": "table_num is required"}, status=400)

    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=['HS256'])
        table = Table.objects.get(table_num=table_num)
        
        if str(table.device_id) != str(payload.get('device_id')):
            return Response({
                "status": "invalid",
                "reason": "Device ID mismatch"
            }, status=403)
            
        return Response({
            "status": "valid",
            "table_num": table.table_num,
            "capacity": table.capacity
        })
        
    except jwt.ExpiredSignatureError:
        return Response({"status": "invalid", "reason": "Token expired"}, status=401)
    except jwt.InvalidTokenError:
        return Response({"status": "invalid", "reason": "Invalid token"}, status=401)
    except Table.DoesNotExist:
        return Response({"status": "invalid", "reason": "Table not found"}, status=404)
    

    
#####################
class AvailableTablesView(generics.ListAPIView):
    queryset = Table.objects.filter(device_id__isnull=True)
    serializer_class = TableSerializer
    permission_classes = [AllowAny]