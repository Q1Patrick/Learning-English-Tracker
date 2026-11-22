"""Input for the cookie session endpoint; no JWTs are issued here."""

from django.contrib.auth import authenticate
from rest_framework import serializers

from common.exceptions import APIError


class StrictBooleanField(serializers.BooleanField):
    def to_internal_value(self, data):
        if type(data) is not bool:
            self.fail("invalid", input=data)
        return data


class SessionLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    remember_me = StrictBooleanField(required=False, default=False)

    def validate(self, attrs):
        if set(self.initial_data) - set(self.fields):
            raise serializers.ValidationError(
                {"non_field_errors": ["Only email, password and remember_me are accepted."]}
            )
        attrs["email"] = attrs["email"].strip().lower()
        user = authenticate(
            request=self.context["request"], email=attrs["email"], password=attrs["password"]
        )
        if user is None or not user.is_active:
            # Cùng lỗi cho email sai, password sai và tài khoản không hoạt động.
            raise APIError(
                "Email or password is incorrect.", "authentication_failed", status_code=401
            )
        attrs["user"] = user
        return attrs
