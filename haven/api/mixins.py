from rest_framework.exceptions import ParseError


class ExtraFilterKwargsMixin:
    """
    Mixin for use in API views which are nested under another detail view url path
    e.g. when `DatasetListAPIView` is used in url
    `"work_packages/<slug:work_packages__uuid>/datasets"` and the resulting dataset should be
    filtered by the associated work package identified by `work_packages__uuid`
    """

    # These must be a valid filter kwarg for the data model being filtered
    # e.g. `work_packages__uuid` is valid for `Dataset`
    filter_kwargs = []

    def get_filter_kwargs(self):
        extra_filters = {}
        for filter_kwarg in self.filter_kwargs:
            if filter_kwarg in self.kwargs:
                extra_filters = {filter_kwarg: self.kwargs[filter_kwarg]}
        return extra_filters


class AllowedPatchFieldsMixin:
    """Mixin for use in DRF UpdateAPIView which defines which fields can be patched"""

    # Fields which can be patched by this view
    allowed_patch_fields = []
    PARSE_ERROR_DETAIL = "Only the following fields can be used with PATCH for this data type: {}"

    def patch(self, request, *args, **kwargs):
        # If there are any fields that are not allowed in `allowed_patch_fields` then raise error
        if set(request.POST.keys()) - set(self.allowed_patch_fields):
            # This results in 400 status code by default
            raise ParseError(detail=self.PARSE_ERROR_DETAIL.format(self.allowed_patch_fields))
        return super().patch(request, *args, **kwargs)
