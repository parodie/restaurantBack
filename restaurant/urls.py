from rest_framework.routers import DefaultRouter
from django.urls import path, include
from restaurant.views import *

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
    path('client/orders/', ClientOrderView.as_view(), name='client-orders'),
]