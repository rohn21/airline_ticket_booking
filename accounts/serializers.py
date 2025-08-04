from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers
from .models import User, Profile
from django.db import transaction


class CustomRegisterSerializer(RegisterSerializer):
    username = None
    first_name = serializers.CharField(required=False, max_length=30)
    last_name = serializers.CharField(required=False, max_length=150)

    # email = serializers.EmailField(required=True)

    def get_cleaned_data(self):
        data = super().get_cleaned_data()

        first_name = self.validated_data.get('first_name', '')
        last_name = self.validated_data.get('last_name', '')

        data['username'] = data['email']  # Use email as username

        data['first_name'] = first_name
        data['last_name'] = last_name

        return data

    @transaction.atomic
    def save(self, request):
        user = super().save(request)
        user.first_name = self.validated_data.get('first_name', '')
        user.last_name = self.validated_data.get('last_name', '')
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "is_active", "is_staff", "is_email_verified"]
        read_only_fields = ["id", "email", "is_active", "is_staff", "is_email_verified"]


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ["id", "user", "first_name", "last_name", "phone_number", "date_of_birth", "profile_pic"]
