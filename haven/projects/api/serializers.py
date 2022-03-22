from rest_framework import serializers

from ..models import Project


class ProjectSerializer(serializers.ModelSerializer):
    participants = serializers.StringRelatedField(many=True)
    work_packages = serializers.StringRelatedField(many=True)

    class Meta:
        model = Project
        fields = [
            "name", "uuid", "description", "archived", "work_packages", "datasets", "participants"
        ]