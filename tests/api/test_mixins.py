import re

import pytest
from rest_framework.exceptions import ParseError

from conftest import MockPostRequest
from haven.api.mixins import AllowedPatchFieldsMixin


class DummyPatchView:
    """Dummy view which has a `patch` function"""

    DUMMY_RESPONSE = "test_patch"

    def patch(self, *args, **kwargs):
        return self.DUMMY_RESPONSE


class DummyPatchViewWithMixin(AllowedPatchFieldsMixin, DummyPatchView):
    """
    A dummy view which uses the `AllowedPatchFieldsMixin` and inherits from a class which has a
    `patch` function
    """

    pass


@pytest.mark.django_db
class TestAllowedPatchFieldsMixin:
    @pytest.mark.parametrize(
        "allowed_patch_fields,patch_body",
        # In each of these cases a key is present in the `patch_body` that is not in
        # `allowed_patch_fields`
        [
            (["a", "b"], {"a": 1, "b": 2, "c": 3}),
            (["a"], {"a": 1, "b": 2}),
            (["a"], {"c": 3}),
            ([], {"c": 3}),
        ],
    )
    def test_parse_error(self, allowed_patch_fields, patch_body):
        """
        Test that the `AllowedPatchFieldsMixin` `patch` function raises a `ParseError` when the keys
        in the POST data are not present in the `allowed_patch_fields` attribute
        """
        mixin = AllowedPatchFieldsMixin()
        mixin.allowed_patch_fields = allowed_patch_fields

        mock_post_request = MockPostRequest(body=patch_body)

        # Assert `ParseError` raised with correct error message
        with pytest.raises(
            ParseError,
            match=re.escape(mixin.PARSE_ERROR_DETAIL.format(mixin.allowed_patch_fields)),
        ):
            mixin.patch(mock_post_request)

    @pytest.mark.parametrize(
        "allowed_patch_fields,patch_body",
        # In each of these cases all keys in the `patch_body` are present in `allowed_patch_fields`
        [
            (["a", "b"], {"a": 1, "b": 2}),
            (["a", "b"], {"a": 1}),
            (["a"], {"a": 1}),
        ],
    )
    def test_patch_allowed(self, allowed_patch_fields, patch_body):
        """
        Test that the `DummyPatchView` `patch` function is called when the `patch_body`
        only contains keys which are present in `allowed_patch_fields`
        """
        view = DummyPatchViewWithMixin()
        view.allowed_patch_fields = allowed_patch_fields

        mock_post_request = MockPostRequest(body=patch_body)

        assert view.patch(mock_post_request) == DummyPatchView.DUMMY_RESPONSE
