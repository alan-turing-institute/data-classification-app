from rest_framework import serializers

from haven.data.models import Dataset


class DatasetSerializer(serializers.ModelSerializer):
    projects = serializers.SlugRelatedField(many=True, read_only=True, slug_field="uuid")
    work_packages = serializers.SlugRelatedField(many=True, read_only=True, slug_field="uuid")
    default_representative = serializers.SlugRelatedField(read_only=True, slug_field="uuid")
    created_by = serializers.SlugRelatedField(read_only=True, slug_field="uuid")

    class Meta:
        model = Dataset
        fields = [
            "name",
            "uuid",
            "description",
            "projects",
            "work_packages",
            "default_representative",
            "created_at",
            "created_by",
        ]
