from django.conf import settings
from django.core.exceptions import ValidationError
from oauth2_provider.models import Application

from haven.api.models import ApplicationProfile
from haven.data.models import Dataset
from haven.projects.models import Project, WorkPackage


# A mapping between the work package tier and dataset expiry time in seconds
WORK_PACKAGE_TIER_EXPIRY_SECONDS_MAP = {
    0: settings.TIER_0_EXPIRY_SECONDS,
    1: settings.TIER_1_EXPIRY_SECONDS,
    2: settings.TIER_2_EXPIRY_SECONDS,
    3: settings.TIER_3_EXPIRY_SECONDS,
    4: settings.TIER_4_EXPIRY_SECONDS,
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


def get_maximum_tier_filter(request, filter_key="work_packages__tier__lte"):
    """
    Function to get the maximum allowed work package tier for a given application from the incoming
    request
    """
    max_tier_filter = {}
    application = Application.objects.filter(id=request._auth.application_id).last()
    if application:
        application_profile = ApplicationProfile.objects.filter(application=application).last()
        if application_profile:
            max_tier_filter[filter_key] = application_profile.maximum_tier

    return max_tier_filter


def get_accessible_datasets(request, extra_filters={}):
    """Function to return queryset of datasets which are accessible to a given user"""
    max_tier_filter = get_maximum_tier_filter(request)

    # Users with certain roles can view all API data regardless of whether they are associated with
    # it or whether the work package is classified
    if request.user.system_permissions.can_view_all_api_data:
        # `max_tier_filter` and `extra_filters` still apply to user that can view all api data
        return safe_filter_and_deduplicate(Dataset, {**max_tier_filter, **extra_filters})

    return safe_filter_and_deduplicate(
        Dataset,
        {
            # User must be participant of work package
            "work_packages__participants__user": request.user,
            # User must be a participant of work packages project
            "work_packages__project__participants__user": request.user,
            # At least one work package must be classified
            "work_packages__tier__gte": 0,
            # Limit work package tier based on requesting application
            **max_tier_filter,
            # Any extra filters, such as a particular work package
            **extra_filters,
        },
    )


def get_accessible_projects(request, extra_filters={}):
    """Function to return queryset of projects which are accessible to a given user"""
    # Users with certain roles can view all API data regardless of whether they are associated with
    # it
    if request.user.system_permissions.can_view_all_api_data:
        return safe_filter_and_deduplicate(Project, extra_filters)

    return safe_filter_and_deduplicate(
        Project,
        {
            # User must be a participant of project
            "participants__user": request.user,
            # Any extra filters
            **extra_filters,
        },
    )


def get_accessible_work_packages(request, extra_filters={}):
    """Function to return queryset of projects which are accessible to a given user"""
    max_tier_filter = get_maximum_tier_filter(request, filter_key="tier__lte")

    # Users with certain roles can view all API data regardless of whether they are associated with
    # it or whether the work package is classified
    if request.user.system_permissions.can_view_all_api_data:
        # `max_tier_filter` and `extra_filters` still apply to user that can view all api data
        return safe_filter_and_deduplicate(WorkPackage, {**max_tier_filter, **extra_filters})

    return safe_filter_and_deduplicate(
        WorkPackage,
        {
            # User must be participant of work package
            "participants__user": request.user,
            # Work package must be classified
            "tier__gte": 0,
            # Limit work package tier based on requesting application
            **max_tier_filter,
            # Any extra filters, such as a particular project
            **extra_filters,
        },
    )
