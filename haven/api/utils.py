from haven.data.models import Dataset
from haven.projects.models import Project, WorkPackage


def get_accessible_datasets(user):
    """Function to return queryset of datasets which are accessible to a given user"""
    queryset = Dataset.objects.all()

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


def get_accessible_projects(user):
    """Function to return queryset of projects which are accessible to a given user"""
    return Project.objects.filter(participants__user=user)


def get_accessible_work_packages(user):
    """Function to return queryset of projects which are accessible to a given user"""
    return WorkPackage.objects.filter(project__participants__user=user, participants__user=user)
