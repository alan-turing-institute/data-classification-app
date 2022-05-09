from django.db.models import Q

from haven.data.models import Dataset


def get_accessible_datasets(user, queryset=None):
    """Function to return queryset of datasets which accessible to a given user"""
    queryset = queryset if queryset is not None else Dataset.objects.all()

    # Requesting user must be a participant in a classified work package associated with dataset
    queryset = queryset.filter(
        Q(work_packages__participants__user=user) & ~Q(work_packages__tier=None),
    )

    return queryset
