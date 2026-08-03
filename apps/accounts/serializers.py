from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
)
from .models import UserProfile

from django.contrib.auth import get_user_model
User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "password",
            "password_confirm",
        )
        read_only_fields = ("id",)
        extra_kwargs = {
            "first_name": {
                "required": False,
                "allow_blank": True,
            },
            "last_name": {
                "required": False,
                "allow_blank": True,
            },
        }

    def validate_email(self, value):
        normalized_email = value.strip().lower()

        if User.objects.filter(
            email__iexact=normalized_email
        ).exists():
            raise serializers.ValidationError(
                "An account with this email already exists."
            )

        return normalized_email

    def validate(self, attrs):
        password = attrs.get("password")
        password_confirm = attrs.get("password_confirm")

        if password != password_confirm:
            raise serializers.ValidationError(
                {
                    "password_confirm": (
                        "The two passwords do not match."
                    )
                }
            )

        temporary_user = User(
            email=attrs.get("email"),
            first_name=attrs.get("first_name", ""),
            last_name=attrs.get("last_name", ""),
        )

        validate_password(
            password=password,
            user=temporary_user,
        )

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")

        user = User.objects.create_user(
            password=password,
            **validated_data,
        )

        UserProfile.objects.create(user=user)

        return user
    
#Login JWT
class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        data["user"] = {
            "id": str(self.user.id),
            "email": self.user.email,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "is_email_verified": self.user.is_email_verified,
        }

        return data
    

# Create the profile serializer
class UserProfileSerializer(serializers.ModelSerializer):
    """Serialize the user's English-learning profile."""

    class Meta:
        model = UserProfile
        fields = (
            "display_name",
            "english_level",
            "daily_target_minutes",
            "learning_goal",
            "timezone",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "created_at",
            "updated_at",
        )
    def validate_daily_target_minutes(self, value):
        if value < 5:
            raise serializers.ValidationError(
                "The daily target must be at least 5 minutes."
            )

        if value > 480:
            raise serializers.ValidationError(
                "The daily target cannot exceed 480 minutes."
            )

        return value

class CurrentUserSerializer(serializers.ModelSerializer):
    """Serialize and update the authenticated user's account and profile."""

    profile = UserProfileSerializer()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "is_email_verified",
            "profile",
        )
        read_only_fields = (
            "id",
            "email",
            "is_email_verified",
        )

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", None)

        instance.first_name = validated_data.get(
            "first_name",
            instance.first_name,
        )
        instance.last_name = validated_data.get(
            "last_name",
            instance.last_name,
        )
        instance.save(
            update_fields=[
                "first_name",
                "last_name",
            ]
        )

        if profile_data is not None:
            profile, _ = UserProfile.objects.get_or_create(
                user=instance
            )

            for field, value in profile_data.items():
                setattr(profile, field, value)

            profile.save()

        return instance