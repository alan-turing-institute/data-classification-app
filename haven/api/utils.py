from haven.data.models import Dataset


def get_accessible_datasets(user):
    """Function to return queryset of datasets which are accessible to a given user"""
    return Dataset.objects.filter(
        # User must be participant of work package
        work_packages__participants__user=user,
        # User must be a participant of work packages project
        work_packages__project__participants__user=user,
        # At least one work package must be classified
        work_packages__tier__gte=0,
    )
