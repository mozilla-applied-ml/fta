from rest_framework import serializers

from ..models import Sample


class SampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sample
        exclude = []


class SampleListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sample
        exclude = ["frozen_page"]
