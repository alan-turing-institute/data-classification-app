from rest_framework import serializers

from haven.identity.api.serializers import UserSerializer
from ..models import Dataset


class DatasetSerializer(serializers.ModelSerializer):
    default_representative = UserSerializer()
    created_by = UserSerializer()

    class Meta:
        model = Dataset
        fields = [
            "uuid","name","description","default_representative","created_at","created_by"
        ]