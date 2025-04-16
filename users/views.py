from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import PermissionDenied
from .models import User
from .serializers import *


class AdminChangePasswordView(generics.UpdateAPIView):
    queryset = User.objects.all() 
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_object(self):
        return self.queryset.get(pk=self.kwargs['pk'])
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = self.get_object()  # Pass the target user to serializer
        return context
    
    def perform_update(self, serializer):
        serializer.save(user=self.get_object())
     
    
class RegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.IsAdminUser]
    
    
class UserUpdateView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserUpdateSerializer
    permission_classes = [permissions.IsAdminUser]
    
class UserDeleteView(generics.DestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserDeleteSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_destroy(self, instance):
        serializer = self.get_serializer(instance)
        serializer.delete(instance)
        return Response({"message": "User deactivated successfully"})
    
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'token': str(refresh.access_token),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'role': user.role
                }
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure the user is authenticated
    
    def post(self, request, *args, **kwargs):
        try:
            # Get the Refresh Token from request headers
            refresh_token = request.data.get('refresh_token')
            
            if refresh_token:
                # Blacklist the refresh token if using blacklisting feature
                token = RefreshToken(refresh_token)
                token.blacklist() 
            else:
                return Response({"detail": "Refresh token is missing"}, status=400)
            
            
                
            return Response({"detail": "Logged out successfully"}, status=200)
        except Exception as e:
            return Response({"detail": str(e)}, status=400)
    