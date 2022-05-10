from haven.data.models import Dataset
from haven.projects.models import Project, WorkPackage


def get_accessible_datasets(user):
    """Function to return queryset of datasets which are accessible to a given user"""
    return Dataset.objects.filter(
        # User must be a participant of dataset's project
        projects__participants__user=user,
        # User must be participant of work package
        work_packages__participants__user=user,
        # User must be a participant of work packages project
        work_packages__project__participants__user=user,
        # At least one work package must be classified
        work_packages__tier__gte=0,
    )


def get_accessible_projects(user):
    """Function to return queryset of projects which are accessible to a given user"""
    return Project.objects.filter(participants__user=user)


def get_accessible_work_packages(user):
    """Function to return queryset of projects which are accessible to a given user"""
    return WorkPackage.objects.filter(project__participants__user=user, participants__user=user)
