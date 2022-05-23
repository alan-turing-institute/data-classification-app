from django.core.exceptions import ValidationError

from haven.data.models import Dataset
from haven.projects.models import Project, WorkPackage


# A mapping between the work package tier and dataset expiry time in seconds
WORK_PACKAGE_TIER_EXPIRY_SECONDS_MAP = {
    0: 60 * 60,  # 1 hour
    1: 24 * 60 * 60,  # 1 day
    2: 2 * 24 * 60 * 60,  # 2 days
    3: 3 * 24 * 60 * 60,  # 3 days
    4: 4 * 24 * 60 * 60,  # 4 days
    5: 5 * 24 * 60 * 60,  # 5 days
}


def safe_filter_and_deduplicate(model_class, filters):
    """
    Function which takes a model_class, applies filters, and removes duplicate items.
    It returns an empty dataset if any ValidationErrors are caught.
    """
    try:
        # Use distinct because when filtering through M2M fields duplicate items can be returned
        return model_class.objects.filter(**filters).distinct()
    # ValidationError can happen when trying to filter by an invalid UUID
    except ValidationError:
        return model_class.objects.none()


def get_accessible_datasets(user, extra_filters={}):
    """Function to return queryset of datasets which are accessible to a given user"""
    return safe_filter_and_deduplicate(
        Dataset,
        {
            # User must be participant of work package
            "work_packages__participants__user": user,
            # User must be a participant of work packages project
            "work_packages__project__participants__user": user,
            # At least one work package must be classified
            "work_packages__tier__gte": 0,
            # Any extra filters, such as a particular work package
            **extra_filters,
        },
    )


def get_accessible_projects(user, extra_filters={}):
    """Function to return queryset of projects which are accessible to a given user"""
    return safe_filter_and_deduplicate(
        Project,
        {
            # User must be a participant of project
            "participants__user": user,
            # Any extra filters
            **extra_filters,
        },
    )


def get_accessible_work_packages(user, extra_filters={}):
    """Function to return queryset of projects which are accessible to a given user"""
    return safe_filter_and_deduplicate(
        WorkPackage,
        {
            # User must be participant of work package
            "participants__user": user,
            # Work package must be classified
            "tier__gte": 0,
            # Any extra filters, such as a particular project
            **extra_filters,
        },
    )
