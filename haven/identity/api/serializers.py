from rest_framework import serializers

from haven.projects.models import Participant
from ..models import User


class UserContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "uuid","first_name","last_name","email","mobile"
        ]


class UserResourceSerializer(serializers.ModelSerializer):
    """Provide a list of projects, workpackages, and datasets
    the user has access to"""

    class Meta:
        model = User
        fields = [
            "uuid","first_name","last_name","email","mobile",
            "participants"
        ]