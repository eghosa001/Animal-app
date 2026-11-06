"""Public account contracts. Never expose internal verification evidence."""
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import SellerProfile, User


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    display_name = serializers.CharField(max_length=100, min_length=2)
    password = serializers.CharField(min_length=10, max_length=128, write_only=True, trim_whitespace=False)

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists")
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class MeSerializer(serializers.ModelSerializer):
    seller_status = serializers.SerializerMethodField()
    email_verified = serializers.BooleanField(source="is_email_verified", read_only=True)

    class Meta:
        model = User
        fields = ("id", "email", "display_name", "email_verified", "seller_status")

    def get_seller_status(self, obj):
        seller = getattr(obj, "seller_profile", None)
        return seller.status if seller else None


class SellerApplySerializer(serializers.Serializer):
    business_name = serializers.CharField(min_length=2, max_length=140)
    adult_attested = serializers.BooleanField()

    def validate_adult_attested(self, value):
        if not value:
            raise serializers.ValidationError("Only eligible adults can apply to sell")
        return value


class SellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerProfile
        fields = ("business_name", "status", "submitted_at", "reviewed_at")
        read_only_fields = fields


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)

    def validate_email(self, value):
        return value.strip().lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    token = serializers.CharField(min_length=1, max_length=256, trim_whitespace=False)
    new_password = serializers.CharField(
        min_length=10, max_length=128, write_only=True, trim_whitespace=False
    )

    def validate_email(self, value):
        return value.strip().lower()
