"""Shared DRF serializer helpers."""

from rest_framework import serializers


class StrictFieldsMixin:
    """Reject unknown input keys on write serializers (mass-assignment guard)."""

    def to_internal_value(self, data):
        if hasattr(data, "keys"):
            allowed = set(self.fields.keys())
            unknown = [key for key in data.keys() if key not in allowed]
            if unknown:
                raise serializers.ValidationError({field: "Unknown field." for field in unknown})
        return super().to_internal_value(data)
