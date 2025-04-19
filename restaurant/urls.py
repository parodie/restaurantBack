from rest_framework.routers import DefaultRouter
from django.urls import path, include
from restaurant.views import (ChefOrderViewSet, WaiterOrderViewSet, ClientCategoryViewSet, ClientDishViewSet, 
                            ClientOrderView, verify_device, LinkDeviceToTableView, 
                            AvailableTablesView, ClientOrderDetailView, 
                            ClientExpireOrdersView, ResetTableView, ClientOrderCancelView)

router = DefaultRouter()
#router.register(r'admin/categories', CategoryViewSet)
#router.register(r'admin/dishes', DishAdminViewSet)
#router.register(r'admin/tables', TableAdminViewSet)

router.register(r'chef/orders', ChefOrderViewSet, basename="chef-orders")
router.register(r'waiter/orders', WaiterOrderViewSet, basename="waiter-orders")

router.register(r'client/categories', ClientCategoryViewSet, basename="client-categories")
router.register(r'client/dishes', ClientDishViewSet, basename="client-dishes")


urlpatterns = [
    path('', include(router.urls)),
    path('tables/', AvailableTablesView.as_view(), name='available-tables'),
    path('client/orders/', ClientOrderView.as_view(), name='client-orders'),
    path('client/orders/<int:pk>/', ClientOrderDetailView.as_view(), name='client-order-detail'),
    path('client/orders/expire/', ClientExpireOrdersView.as_view(), name='expire-orders'),
    path('client/orders/<int:pk>/cancel/', ClientOrderCancelView.as_view(), name='client-order-cancel'),
    path('client/resetTable/', ResetTableView.as_view(), name='reset-table-device'),
    # Table-device linking
    path('link-table/', LinkDeviceToTableView.as_view(), name='link-table'),
    # Verify device
    path('verify-device/', verify_device, name='verify-device'),
]