from rest_framework import serializers

from haven.identity.api.serializers import UserSerializer
from haven.data.api.serializers import DatasetSerializer
from ..models import Project, Participant, WorkPackage


class ParticipantSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = Participant
        fields = [
            "uuid","role","user"
        ]

class WorkPackageSerializer(serializers.ModelSerializer):
    participants = ParticipantSerializer(many=True)
    datasets = DatasetSerializer(many=True)

    class Meta:
        model = WorkPackage
        fields = [
            "uuid","name","description","participants","datasets","status","tier"
        ]


class ProjectSerializer(serializers.ModelSerializer):
    participants = ParticipantSerializer(many=True)
    work_packages = WorkPackageSerializer(many=True)
    datasets = DatasetSerializer(many=True)

    class Meta:
        model = Project
        fields = [
            "name", "uuid", "description", "archived", "work_packages", "datasets", "participants"
        ]