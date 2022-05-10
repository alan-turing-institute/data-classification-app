from rest_framework import serializers

from haven.api.utils import get_accessible_work_packages
from haven.data.models import Dataset
from haven.projects.models import Project, WorkPackage


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


class ProjectSerializer(serializers.ModelSerializer):
    """
    Class for converting a Project model instance into a JSON representation.
    To be used with DRF API views.
    """

    datasets = serializers.SlugRelatedField(many=True, read_only=True, slug_field="uuid")
    work_packages = serializers.SerializerMethodField()
    created_by = serializers.SlugRelatedField(read_only=True, slug_field="uuid")

    def get_work_packages(self, project):
        """
        Function to get accessible work packages, this ensures that only classified work packages
        are exposed over project API
        """
        return (
            get_accessible_work_packages(self.context["request"]._auth.user)
            .filter(project=project)
            .values_list("uuid", flat=True)
        )

    class Meta:
        model = Project
        fields = [
            "name",
            "uuid",
            "description",
            "datasets",
            "work_packages",
            "archived",
            "created_at",
            "created_by",
        ]


class WorkPackageSerializer(serializers.ModelSerializer):
    """
    Class for converting a WorkPackage model instance into a JSON representation.
    To be used with DRF API views.
    """

    datasets = serializers.SlugRelatedField(many=True, read_only=True, slug_field="uuid")
    project = serializers.SlugRelatedField(read_only=True, slug_field="uuid")
    created_by = serializers.SlugRelatedField(read_only=True, slug_field="uuid")

    class Meta:
        model = WorkPackage
        fields = [
            "name",
            "uuid",
            "description",
            "project",
            "datasets",
            "status",
            "tier",
            "created_at",
            "created_by",
        ]
