from unittest.mock import patch

import pytest

from core import recipes
from identity.graph import user_client


@pytest.mark.django_db
@patch('identity.graph.OAuth2Session')
def test_authenticated_client(mockSession, user1):
    token = {'a': 'b'}
    user1.social_auth.add(recipes.social_auth.make(extra_data=token))

    ret = user_client(user1)

    mockSession.assert_called_with(token=token)
    assert ret._session == mockSession.return_value
