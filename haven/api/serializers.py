from rest_framework import serializers

from haven.data.models import Dataset


class DatasetSerializer(serializers.ModelSerializer):
    """
    Class for converting a Dataset model instance into a JSON representation.
    To be used with DRF API views.
    """

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
