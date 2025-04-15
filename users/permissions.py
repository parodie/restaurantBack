
#class IsAdmin(permissions.BasePermission):
    
#    def has_permission(self, request, view):
#        return request.user.role == 'admin'


#class IsChef(permissions.BasePermission):
    
#    def has_permission(self, request, view):
#        return request.user.role == 'chef'


#class IsWaiter(permissions.BasePermission):
    
#    def has_permission(self, request, view):
#        return request.user.role == 'waiter'
    
# users/permissions.py

from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from django.conf import settings
from django.contrib.auth import get_user_model
from restaurant.models import *

User = get_user_model()

class RoleRequired(BasePermission):
    """Base permission class for role-based access"""
    role = None  
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            raise PermissionDenied('Authentication required')
            
        if not hasattr(request.user, 'role'):
            raise PermissionDenied('Invalid user type')
            
        if request.user.role == self.role :
            return True
            
        raise PermissionDenied(f'{self.role.capitalize()} access required')

class IsAdmin(RoleRequired):
    """Requires admin role"""
    role = User.Role.ADMIN

class IsChef(RoleRequired):
    """Requires chef role (or admin)"""
    role = User.Role.CHEF

class IsWaiter(RoleRequired):
    """Requires waiter role (or admin)"""
    role = User.Role.WAITER

class HasKitchenAccess(BasePermission):
    """Requires kitchen access (chef or admin)"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            raise PermissionDenied('Authentication required')
            
        if not hasattr(request.user, 'has_kitchen_access'):
            raise PermissionDenied('Invalid user type')
            
        if request.user.has_kitchen_access():
            return True
            
        raise PermissionDenied('Kitchen staff access required')

class HasServingAccess(BasePermission):
    """Requires serving access (waiter or admin)"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            raise PermissionDenied('Authentication required')
            
        if not hasattr(request.user, 'has_serving_access'):
            raise PermissionDenied('Invalid user type')
            
        if request.user.has_serving_access():
            return True
            
        raise PermissionDenied('Serving staff access required')
    
class IsTableDevice(BasePermission):
    """Allows access only from registered table devices"""
    def has_permission(self, request, view):
        return hasattr(request, 'table')

class IsAdminOrTableDevice(BasePermission):
    """Allows admins or registered table devices"""
    def has_permission(self, request, view):
        return (request.user.is_authenticated and request.user.is_admin) or hasattr(request, 'table')
    
class IsTableDevice(BasePermission):
    """
    Permission to only allow access to table devices.
    """
    def has_permission(self, request, view):
        device_id = request.headers.get('X-Device-ID')
        if not device_id:
            return False
        
        # Check if there's a table with this device ID
        table_exists = Table.objects.filter(device_id=device_id, is_active=True).exists()
        if table_exists:
            # Attach the table to the request for later use
            request.table = Table.objects.get(device_id=device_id)
        return table_exists

