from django.core.exceptions import ObjectDoesNotExist
from oauth2_provider.contrib.rest_framework import TokenHasScope
from oauth2_provider.views import ApplicationRegistration, ApplicationUpdate
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from haven.api.forms import ApplicationCreateOrUpdateForm
from haven.api.mixins import ExtraFilterKwargsMixin
from haven.api.serializers import (
    DatasetExpirySerializer,
    DatasetSerializer,
    ProjectSerializer,
    WorkPackageSerializer,
)
from haven.api.utils import (
    get_accessible_datasets,
    get_accessible_projects,
    get_accessible_work_packages,
)


class DatasetListAPIView(ExtraFilterKwargsMixin, generics.ListAPIView):
    """API view to return a list of datasets that the requesting user has access to"""

    serializer_class = DatasetSerializer
    required_scopes = ["read"]
    permission_classes = [IsAuthenticated, TokenHasScope]
    filter_kwargs = ["work_packages__uuid", "projects__uuid"]

    def get_queryset(self):
        """Return all datasets accessible by requesting OAuth user"""
        return get_accessible_datasets(self.request, extra_filters=self.get_filter_kwargs())


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
        return get_accessible_datasets(self.request, extra_filters=self.get_filter_kwargs())


class DatasetExpiryAPIView(generics.RetrieveAPIView):
    """
    API view read the expiry time of a dataset for the requesting user which depends on the tier of
    the associated work packages
    """

    serializer_class = DatasetExpirySerializer
    required_scopes = ["read"]
    permission_classes = [IsAuthenticated, TokenHasScope]
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"

    def get_queryset(self):
        """Return all datasets accessible by requesting OAuth user"""
        return get_accessible_datasets(self.request)


class ProjectListAPIView(ExtraFilterKwargsMixin, generics.ListAPIView):
    """API view to return a list of projects that the requesting user has access to"""

    serializer_class = ProjectSerializer
    required_scopes = ["read"]
    permission_classes = [IsAuthenticated, TokenHasScope]

    def get_queryset(self):
        """Return all datasets accessible by requesting OAuth user"""
        return get_accessible_projects(self.request, extra_filters=self.get_filter_kwargs())


class ProjectDetailAPIView(ExtraFilterKwargsMixin, generics.RetrieveAPIView):
    """API view to return the details of a project that the requesting user has access to"""

    serializer_class = ProjectSerializer
    required_scopes = ["read"]
    permission_classes = [IsAuthenticated, TokenHasScope]
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"

    def get_queryset(self):
        """Return all projects accessible by requesting OAuth user"""
        return get_accessible_projects(self.request, extra_filters=self.get_filter_kwargs())


class WorkPackageListAPIView(ExtraFilterKwargsMixin, generics.ListAPIView):
    """API view to return a list of work packages that the requesting user has access to"""

    serializer_class = WorkPackageSerializer
    required_scopes = ["read"]
    permission_classes = [IsAuthenticated, TokenHasScope]
    filter_kwargs = ["project__uuid"]

    def get_queryset(self):
        """Return all datasets accessible by requesting OAuth user"""
        return get_accessible_work_packages(self.request, extra_filters=self.get_filter_kwargs())


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
        return get_accessible_work_packages(self.request, extra_filters=self.get_filter_kwargs())


# To see original `ApplicationRegistration` view see:
# https://github.com/jazzband/django-oauth-toolkit/blob/master/oauth2_provider/views/application.py
class CustomApplicationRegistration(ApplicationRegistration):
    """View used to register a new Oauth client Application"""

    def get_form_class(self):
        """Returns the form class which also saves information to ApplicationProfile model"""
        return ApplicationCreateOrUpdateForm


# To see original `ApplicationUpdate` view see:
# https://github.com/jazzband/django-oauth-toolkit/blob/master/oauth2_provider/views/application.py
class CustomClientApplicationUpdate(ApplicationUpdate):
    """View used to update an existing Oauth client Application"""

    def get_form_class(self):
        """Returns the form class which also saves information to ApplicationProfile model"""
        return ApplicationCreateOrUpdateForm

    def get_initial(self):
        initial = super().get_initial()
        try:
            initial["maximum_tier"] = self.object.profile.maximum_tier
        # Incase no `ApplicationProfile` associated with this `Application`
        # e.g. in a DB which existed before this model was introduced
        except ObjectDoesNotExist:
            pass

        return initial
