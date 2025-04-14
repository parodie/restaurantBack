from rest_framework import serializers
from .models import User
from django.contrib.auth import authenticate

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'password2', 'role']
        extra_kwargs = {
            'password': {'write_only': True},
            'password2': {'write_only': True},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        if not request or not request.user.is_superuser:
            raise PermissionDenied("Only administrators can create users")
        
        validated_data.pop('password2')
        return User.objects.create_user(**validated_data)
    
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    new_password2 = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "New password fields didn't match."})
        return attrs

    def validate_old_password(self, value):
        user = self.context.get('user')    
        if not user:
            raise serializers.ValidationError("User not found")
          
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value

    def save(self, **kwargs):
        request = self.context.get('request')
        
        # Check if the logged-in user is an admin
        if not request.user.is_superuser:
            raise PermissionDenied("Only administrators can change other users' passwords")

        # Get the target user whose password is being changed (from kwargs or context)
        user = kwargs.get('user') or self.context.get('user')
        if not user:
            raise PermissionDenied("No user specified for password change.")

        # Set and save the new password
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
    

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'is_active']

    def update(self, instance, validated_data):
        request = self.context.get('request')
        if not request or not request.user.is_superuser:
            raise PermissionDenied("Only administrators can update users")
        return super().update(instance, validated_data)

class UserDeleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = []

    def delete(self, instance):
        request = self.context.get('request')
        if not request or not request.user.is_superuser:
            raise PermissionDenied("Only administrators can delete users")
        
        instance.is_active = False
        instance.save()
        return instance
    
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        user = authenticate(username=attrs.get('username'), password=attrs.get('password'))
        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        if not user.is_active:
            raise serializers.ValidationError("User is inactive.")
        
        attrs['user'] = user
        return attrs