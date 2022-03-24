from rest_framework import serializers

from haven.identity.api.serializers import UserContactSerializer
from ..models import Dataset


class DatasetSerializer(serializers.ModelSerializer):
    default_representative = UserContactSerializer()
    created_by = UserContactSerializer()

    class Meta:
        model = Dataset
        fields = [
            "uuid","name","description","default_representative","created_at","created_by"
        ]