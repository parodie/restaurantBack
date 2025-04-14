from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import *

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'role')

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'role' in self.fields:
            self.fields['role'].disabled = True
        
        if self.instance:
            if self.instance.role == User.Role.ADMIN:
                if 'is_staff' in self.fields:
                    self.fields['is_staff'].initial = True
                if 'is_superuser' in self.fields:
                    self.fields['is_superuser'].initial = True
            else:
                if 'is_superuser' in self.fields:
                    del self.fields['is_superuser']
                if 'is_staff' in self.fields:
                    self.fields['is_staff'].disabled = True
                    self.fields['is_staff'].initial = False

class UserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm

    list_display = ('username', 'role', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser')
    readonly_fields = ('date_joined', 'last_login', 'role')
    search_fields = ('username',)
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Permissions', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('date_joined', 'last_login')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'role'),
        }),
    )

    def get_fieldsets(self, request, obj=None):
        # Ensure self.fields is properly initialized
        fieldsets = super().get_fieldsets(request, obj)

        if obj:  # Editing an existing user
            if hasattr(self, 'fields') and self.fields:  # Check if fields exist
                if obj.role == User.Role.ADMIN:
                    # Disable the role field for admins
                    self.fields['role'].disabled = True
                    self.fields['is_staff'].initial = True
                    self.fields['is_superuser'].initial = True
                elif obj.role == User.Role.CHEF:
                    # Disable the role field for chefs
                    self.fields['role'].disabled = True
                    self.fields['is_staff'].initial = False
                    self.fields['is_superuser'].initial = False
                elif obj.role == User.Role.WAITER:
                    # Disable the role field for waiters
                    self.fields['role'].disabled = True
                    self.fields['is_staff'].initial = False
                    self.fields['is_superuser'].initial = False
            else:
                print("Warning: self.fields is None or not initialized properly.")
        return fieldsets


    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if obj:
            readonly_fields += ('role',)  
            if obj.role == User.Role.CHEF or obj.role == User.Role.WAITER or obj.role == User.Role.ADMIN:
                readonly_fields += ('is_staff', 'is_superuser',)
        return readonly_fields

    def save_model(self, request, obj, form, change):
        # Automatically set is_staff and is_superuser for admins
        if obj.role == User.Role.ADMIN:
            obj.is_staff = True
            obj.is_superuser = True
        else:
            obj.is_staff = False
            obj.is_superuser = False
        super().save_model(request, obj, form, change)

# Register the UserAdmin for User and the role-based admin classes for each role
admin.site.register(User, UserAdmin)
admin.site.register(Admin, UserAdmin)
admin.site.register(Chef, UserAdmin)
admin.site.register(Waiter, UserAdmin)