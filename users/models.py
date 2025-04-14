from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, username, password=None, password2=None, role="Chef", **extra_fields):
        if not username:
            raise ValueError("Users must have a username")
        
        if not role:
            raise ValueError("Users must have a role")
        
        role = role.lower()  
        
        if role == User.Role.ADMIN:
            extra_fields.setdefault("is_staff", True)
            extra_fields.setdefault("is_superuser", True)
        else:
            extra_fields.setdefault("is_staff", False)
            extra_fields.setdefault("is_superuser", False)
            
        user = self.model(username=username, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("Users must have a username")
    
        extra_fields.setdefault("role", User.Role.ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        
        # Pour éviter que Django ne demande le champ role pendant createsuperuser
        if "role" in extra_fields and extra_fields["role"] != User.Role.ADMIN:
            raise ValueError("Superuser must have role=admin.")
        
        # Gérer le cas où password2 n'est pas fourni pour createsuperuser
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        WAITER = 'waiter', 'Waiter'
        CHEF = 'chef', 'Chef'
    
    username = models.CharField(max_length=150, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)  # Fixed this line
    updated_at = models.DateTimeField(auto_now=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CHEF
    )

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["role"]
    
    def __str__(self):
        return self.username
        
    def clean(self):
        super().clean()
        if self.role not in [role[0] for role in self.Role.choices]:
            raise ValidationError({'role': f'Invalid role. Must be one of: {[role[0] for role in self.Role.choices]}'})
    
    def get_full_name(self):
        return self.username
    
    def get_short_name(self):
        return self.username
    
    def delete(self, *args, **kwargs):
        """Soft delete"""
        self.is_active = False
        self.save()
    
    def is_admin(self):
        return self.role == self.Role.ADMIN
    
    def is_chef(self):
        return self.role == self.Role.CHEF
    
    def is_waiter(self):
        return self.role == self.Role.WAITER
    
    @property
    def has_kitchen_access(self):
        return self.is_chef()
    
    @property
    def has_serving_access(self):
        return self.is_waiter


# Proxy models
class AdminManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role=User.Role.ADMIN)

class Admin(User):
    objects = AdminManager()

    class Meta:
        proxy = True
        verbose_name = 'Administrator'
        verbose_name_plural = 'Administrators'
        
    def save(self, *args, **kwargs):
        self.role = User.Role.ADMIN
        super().save(*args, **kwargs)

class ChefManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role=User.Role.CHEF)

class Chef(User):
    objects = ChefManager()

    class Meta:
        proxy = True
        verbose_name = 'Chef'
        verbose_name_plural = 'Chefs'
    
    def save(self, *args, **kwargs):
        self.role = User.Role.CHEF
        super().save(*args, **kwargs)
        
class WaiterManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role=User.Role.WAITER)

class Waiter(User):
    objects = WaiterManager()

    class Meta:
        proxy = True
        verbose_name = 'Waiter'
        verbose_name_plural = 'Waiters'
    
    def save(self, *args, **kwargs):
        self.role = User.Role.WAITER
        super().save(*args, **kwargs)