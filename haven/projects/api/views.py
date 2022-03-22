from rest_framework.generics import (
    RetrieveAPIView,
    ListAPIView
)
from rest_framework.permissions import IsAuthenticated

from ..models import Project
from .serializers import ProjectSerializer


class ProjectListAPIView(ListAPIView):
    queryset = Project.objects.all()
    permission_classes = (IsAuthenticated, )
    serializer_class = ProjectSerializer
    lookup_field = "uuid"

class ProjectRetrieveAPIView(RetrieveAPIView):
    queryset = Project.objects.all()
    permission_classes = (IsAuthenticated, )
    serializer_class = ProjectSerializer
    lookup_field = "uuid"