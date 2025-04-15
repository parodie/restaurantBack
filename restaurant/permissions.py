# users/permissions.py

from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from django.conf import settings
from django.contrib.auth import get_user_model

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