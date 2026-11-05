from rest_framework import serializers

from .models import Species


class SpeciesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Species
        fields = ("id", "slug", "name", "category", "trade_enabled")
        read_only_fields = fields
