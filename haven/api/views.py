from oauth2_provider.contrib.rest_framework import TokenHasScope
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from haven.api.serializers import DatasetSerializer
from haven.data.utils import get_accessible_datasets


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
