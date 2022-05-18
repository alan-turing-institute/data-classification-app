from django.conf import settings
from django.urls import reverse
from rest_framework import serializers

from haven.api.utils import (
    get_accessible_datasets,
    get_accessible_projects,
    get_accessible_work_packages,
)
from haven.data.models import Dataset
from haven.projects.models import Project, WorkPackage


class DatasetSerializer(serializers.ModelSerializer):
    """
    Class for converting a Dataset model instance into a JSON representation.
    To be used with DRF API views.
    """

    projects = serializers.SlugRelatedField(many=True, read_only=True, slug_field="uuid")
    work_packages = serializers.SerializerMethodField()
    default_representative = serializers.SlugRelatedField(read_only=True, slug_field="uuid")
    default_representative_email = serializers.SerializerMethodField()
    authorization_url = serializers.SerializerMethodField()
    created_by = serializers.SlugRelatedField(read_only=True, slug_field="uuid")

    def get_work_packages(self, dataset):
        """Function to get accessible work packages that this dataset is associated with"""
        return get_accessible_work_packages(
            self.context["request"]._auth.user, extra_filters={"datasets": dataset}
        ).values_list("uuid", flat=True)

    def get_projects(self, dataset):
        """Function to get accessible projects that this dataset is associated with"""
        return get_accessible_projects(
            self.context["request"]._auth.user, extra_filters={"datasets": dataset}
        ).values_list("uuid", flat=True)

    def get_default_representative_email(self, dataset):
        """Function to the datasets default representatives email"""
        return dataset.default_representative.email if dataset.default_representative else ""

    def get_authorization_url(self, dataset):
        """Function to get the authorization url for the dataset"""
        return f"{settings.SITE_URL}{reverse('api:dataset_detail', kwargs={'uuid': dataset.uuid})}"

    class Meta:
        model = Dataset
        fields = [
            "name",
            "uuid",
            "description",
            "projects",
            "work_packages",
            "default_representative",
            "default_representative_email",
            "authorization_url",
            "host",
            "storage_path",
            "created_at",
            "created_by",
        ]


class ProjectSerializer(serializers.ModelSerializer):
    """
    Class for converting a Project model instance into a JSON representation.
    To be used with DRF API views.
    """

    datasets = serializers.SerializerMethodField()
    work_packages = serializers.SerializerMethodField()
    created_by = serializers.SlugRelatedField(read_only=True, slug_field="uuid")

    def get_datasets(self, project):
        """Function to get accessible datasets that this project is associated with"""
        return get_accessible_datasets(
            self.context["request"]._auth.user, extra_filters={"projects": project}
        ).values_list("uuid", flat=True)

    def get_work_packages(self, project):
        """Function to get accessible work packages that this project is associated with"""
        return get_accessible_work_packages(
            self.context["request"]._auth.user, extra_filters={"project": project}
        ).values_list("uuid", flat=True)

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

    # If work package is classified then all related datasets are accessible,
    # therefore no need for custom function here
    datasets = serializers.SlugRelatedField(many=True, read_only=True, slug_field="uuid")
    # If work package is classified then its project is accessible,
    # therefore no need for custom function here
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
