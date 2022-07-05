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
