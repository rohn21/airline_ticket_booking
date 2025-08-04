from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from core.models import BaseModel


class UserManager(BaseUserManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class AllUserManager(UserManager):
    def get_queryset(self):
        return super(BaseUserManager, self).get_queryset()  # includes soft-deleted


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()
    all_objects = AllUserManager()

    def __str__(self):
        return self.email


def user_profile_pic_path(instance, filename):
    return f"profile_pics/{instance.user.id}/{filename}"

class Profile(BaseModel):
    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE, related_name="profile")
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=15, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[("male", "Male"), ("female", "Female"), ("other", "Other")], blank=True)
    address = models.TextField(blank=True)
    country = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=50, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    nationality = models.CharField(max_length=50, blank=True)
    profile_pic = models.ImageField(upload_to=user_profile_pic_path, null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.user.email})"
