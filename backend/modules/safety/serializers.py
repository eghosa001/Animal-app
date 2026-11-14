"""Public report receipt and private block list never expose third-party email."""
from rest_framework import serializers

from .models import SafetyReport, UserBlock


class BlockReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBlock
        fields = ("id", "blocked", "created_at")
        read_only_fields = fields


class BlockCreateSerializer(serializers.Serializer):
    blocked_user_id = serializers.UUIDField()


class ReportCreateSerializer(serializers.Serializer):
    target_type = serializers.ChoiceField(
        choices=("video", "listing", "message", "user"),
    )
    target_id = serializers.UUIDField()
    category = serializers.ChoiceField(choices=SafetyReport.Category.choices)
    detail = serializers.CharField(
        min_length=20, max_length=1500, trim_whitespace=True,
    )


class ReportReadSerializer(serializers.ModelSerializer):
    target_type = serializers.SerializerMethodField()

    class Meta:
        model = SafetyReport
        fields = ("id", "target_type", "category", "status", "created_at")
        read_only_fields = fields

    def get_target_type(self, obj):
        for field in ("video", "listing", "message", "subject_user"):
            if getattr(obj, f"{field}_id") is not None:
                return "user" if field == "subject_user" else field
        return "unknown"
