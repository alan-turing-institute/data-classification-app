from rest_framework.generics import (
    RetrieveAPIView,
    ListAPIView
)
from rest_framework.permissions import IsAuthenticated

from ..models import User
from .serializers import UserContactSerializer, UserResourceSerializer


class UserListAPIView(ListAPIView):
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated, )
    serializer_class = UserContactSerializer
    lookup_field = "uuid"

class UserResourceAPIView(RetrieveAPIView):
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated, )
    serializer_class = UserResourceSerializer
    lookup_field = "uuid"