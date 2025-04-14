from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import *

urlpatterns = [
    # Authentication URLs
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User management URLs
    path('users/register/', RegistrationView.as_view(), name='register'),
    path('users/<int:pk>/change-password/', AdminChangePasswordView.as_view(), name='change-password'),
    path('users/<int:pk>/update/', UserUpdateView.as_view(), name='update-user'),
    path('users/<int:pk>/delete/', UserDeleteView.as_view(), name='delete-user'),
    path('users/<int:pk>/logout/', LogoutView.as_view(), name='logout'),
]