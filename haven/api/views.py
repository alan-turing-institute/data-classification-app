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


class ExtraFilterKwargsMixin:
    """
    Mixin for use in API views which are nested under another detail view url path
    e.g. when `DatasetListAPIView` is used in url
    `"work_packages/<slug:work_packages__uuid>/datasets"` and the resulting dataset should be
    filtered by the associated work package identified by `work_packages__uuid`
    """

    filter_kwargs = ["work_packages__uuid"]

    def get_filter_kwargs(self):
        extra_filters = {}
        for filter_kwarg in self.filter_kwargs:
            if filter_kwarg in self.kwargs:
                extra_filters = {filter_kwarg: self.kwargs[filter_kwarg]}
        return extra_filters


class DatasetListAPIView(ExtraFilterKwargsMixin, generics.ListAPIView):
    """API view to return a list of datasets that the requesting user has access to"""

    serializer_class = DatasetSerializer
    required_scopes = ["read"]
    permission_classes = [IsAuthenticated, TokenHasScope]
    filter_kwargs = ["work_packages__uuid", "projects__uuid"]

    def get_queryset(self):
        """Return all datasets accessible by requesting OAuth user"""
        return get_accessible_datasets(
            self.request._auth.user, extra_filters=self.get_filter_kwargs()
        )


class DatasetDetailAPIView(ExtraFilterKwargsMixin, generics.RetrieveAPIView):
    """API view to return the details of a dataset that the requesting user has access to"""

    serializer_class = DatasetSerializer
    required_scopes = ["read"]
    permission_classes = [IsAuthenticated, TokenHasScope]
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"
    filter_kwargs = ["work_packages__uuid", "projects__uuid"]

    def get_queryset(self):
        """Return all datasets accessible by requesting OAuth user"""
        return get_accessible_datasets(
            self.request._auth.user, extra_filters=self.get_filter_kwargs()
        )


class ProjectListAPIView(ExtraFilterKwargsMixin, generics.ListAPIView):
    """API view to return a list of projects that the requesting user has access to"""

    serializer_class = ProjectSerializer
    required_scopes = ["read"]
    permission_classes = [IsAuthenticated, TokenHasScope]
    filter_kwargs = []

    def get_queryset(self):
        """Return all datasets accessible by requesting OAuth user"""
        return get_accessible_projects(
            self.request._auth.user, extra_filters=self.get_filter_kwargs()
        )


class ProjectDetailAPIView(ExtraFilterKwargsMixin, generics.RetrieveAPIView):
    """API view to return the details of a Project that the requesting user has access to"""

    serializer_class = ProjectSerializer
    required_scopes = ["read"]
    permission_classes = [IsAuthenticated, TokenHasScope]
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"
    filter_kwargs = []

    def get_queryset(self):
        """Return all projects accessible by requesting OAuth user"""
        return get_accessible_projects(
            self.request._auth.user, extra_filters=self.get_filter_kwargs()
        )


class WorkPackageListAPIView(ExtraFilterKwargsMixin, generics.ListAPIView):
    """API view to return a list of work packages that the requesting user has access to"""

    serializer_class = WorkPackageSerializer
    required_scopes = ["read"]
    permission_classes = [IsAuthenticated, TokenHasScope]
    filter_kwargs = ["project__uuid"]

    def get_queryset(self):
        """Return all datasets accessible by requesting OAuth user"""
        return get_accessible_work_packages(
            self.request._auth.user, extra_filters=self.get_filter_kwargs()
        )


class WorkPackageDetailAPIView(ExtraFilterKwargsMixin, generics.RetrieveAPIView):
    """API view to return the details of a WorkPackage that the requesting user has access to"""

    serializer_class = WorkPackageSerializer
    required_scopes = ["read"]
    permission_classes = [IsAuthenticated, TokenHasScope]
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"
    filter_kwargs = ["project__uuid"]

    def get_queryset(self):
        """Return all work packages accessible by requesting OAuth user"""
        return get_accessible_work_packages(
            self.request._auth.user, extra_filters=self.get_filter_kwargs()
        )
