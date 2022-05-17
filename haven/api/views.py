from oauth2_provider.contrib.rest_framework import TokenHasScope
from rest_framework import generics
from rest_framework.exceptions import ParseError
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

    # These must be a valid filter kwarg for the data model being filtered
    # e.g. `work_packages__uuid` is valid for `Dataset`
    filter_kwargs = []

    def get_filter_kwargs(self):
        extra_filters = {}
        for filter_kwarg in self.filter_kwargs:
            if filter_kwarg in self.kwargs:
                extra_filters = {filter_kwarg: self.kwargs[filter_kwarg]}
        return extra_filters


class AllowedPatchFieldsMixin:
    """Mixin for use in DRF UpdateAPIView which defines which fields can be patched"""

    # Fields which can be patched by this view
    allowed_patch_fields = []
    PARSE_ERROR_DETAIL = "Only the following fields can be used with PATCH for this data type: {}"

    def patch(self, request, *args, **kwargs):
        # If there are any fields that are now allowed raise error response,
        # which result in 400 status code by default
        if set(request.POST.keys()) - set(self.allowed_patch_fields):
            raise ParseError(detail=self.PARSE_ERROR_DETAIL.format(self.allowed_patch_fields))
        return super().patch(request, *args, **kwargs)


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


class DatasetRegisterAPIView(AllowedPatchFieldsMixin, generics.UpdateAPIView):
    serializer_class = DatasetSerializer
    required_scopes = ["write"]
    permission_classes = [IsAuthenticated, TokenHasScope]
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"
    # Fields which can be patched by this view
    allowed_patch_fields = ["host", "storage_path"]

    def get_queryset(self):
        """Return all datasets accessible by requesting OAuth user"""
        return get_accessible_datasets(self.request._auth.user)


class ProjectListAPIView(ExtraFilterKwargsMixin, generics.ListAPIView):
    """API view to return a list of projects that the requesting user has access to"""

    serializer_class = ProjectSerializer
    required_scopes = ["read"]
    permission_classes = [IsAuthenticated, TokenHasScope]

    def get_queryset(self):
        """Return all datasets accessible by requesting OAuth user"""
        return get_accessible_projects(
            self.request._auth.user, extra_filters=self.get_filter_kwargs()
        )


class ProjectDetailAPIView(ExtraFilterKwargsMixin, generics.RetrieveAPIView):
    """API view to return the details of a project that the requesting user has access to"""

    serializer_class = ProjectSerializer
    required_scopes = ["read"]
    permission_classes = [IsAuthenticated, TokenHasScope]
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"

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
    """API view to return the details of a work package that the requesting user has access to"""

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
