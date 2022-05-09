from haven.data.models import Dataset


def get_accessible_datasets(user, queryset=None):
    """Function to return queryset of datasets which are accessible to a given user"""
    queryset = queryset if queryset is not None else Dataset.objects.all()

    # NOTE: This could possibly be done with the ORM to be more performant but it would be a
    # complex query, for now we will use Python
    accessible_dataset_ids = set()

    for dataset in queryset:
        # User must be a participant in the dataset's project
        for project in dataset.projects.filter(participants__user=user):
            if dataset.id in accessible_dataset_ids:
                break

            if (
                # Projects work package must be classified
                project.work_packages.exclude(tier=None)
                # and associated with user and dataset
                .filter(participants__user=user, datasets=dataset).exists()
            ):
                accessible_dataset_ids.add(dataset.id)
                break

    return queryset.filter(id__in=accessible_dataset_ids)
