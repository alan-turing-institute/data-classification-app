from oauth2_provider.contrib.rest_framework import TokenHasScope
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from haven.api.serializers import (
    DatasetSerializer,
    ProjectSerializer,
    WorkPackageSerializer,
)
from haven.api.utils import (
    get_accessible_datasets,
    get_accessible_projects,
    get_accessible_work_packages,
)


class DatasetListAPIView(generics.ListAPIView):
    """API view to return a list of datasets that the requesting user has access to"""

    serializer_class = DatasetSerializer
    required_scopes = ["read"]
    permission_classes = [IsAuthenticated, TokenHasScope]

    def get_queryset(self):
        """Return all datasets accessible by requesting OAuth user"""
        return get_accessible_datasets(self.request._auth.user)


class DatasetDetailAPIView(generics.RetrieveAPIView):
    """API view to return the details of a dataset that the requesting user has access to"""

    serializer_class = DatasetSerializer
    required_scopes = ["read"]
    permission_classes = [IsAuthenticated, TokenHasScope]
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"

    def get_queryset(self):
        """Return all datasets accessible by requesting OAuth user"""
        return get_accessible_datasets(self.request._auth.user)


class ProjectListAPIView(generics.ListAPIView):
    """API view to return a list of projects that the requesting user has access to"""

    serializer_class = ProjectSerializer
    required_scopes = ["read"]
    permission_classes = [IsAuthenticated, TokenHasScope]

    def get_queryset(self):
        """Return all datasets accessible by requesting OAuth user"""
        return get_accessible_projects(self.request._auth.user)


class ProjectDetailAPIView(generics.RetrieveAPIView):
    """API view to return the details of a Project that the requesting user has access to"""

    serializer_class = ProjectSerializer
    required_scopes = ["read"]
    permission_classes = [IsAuthenticated, TokenHasScope]
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"

    def get_queryset(self):
        """Return all projects accessible by requesting OAuth user"""
        return get_accessible_projects(self.request._auth.user)


class WorkPackageListAPIView(generics.ListAPIView):
    """API view to return a list of work packages that the requesting user has access to"""

    serializer_class = WorkPackageSerializer
    required_scopes = ["read"]
    permission_classes = [IsAuthenticated, TokenHasScope]

    def get_queryset(self):
        """Return all datasets accessible by requesting OAuth user"""
        return get_accessible_work_packages(self.request._auth.user)


class WorkPackageDetailAPIView(generics.RetrieveAPIView):
    """API view to return the details of a WorkPackage that the requesting user has access to"""

    serializer_class = WorkPackageSerializer
    required_scopes = ["read"]
    permission_classes = [IsAuthenticated, TokenHasScope]
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"

    def get_queryset(self):
        """Return all work packages accessible by requesting OAuth user"""
        return get_accessible_work_packages(self.request._auth.user)
