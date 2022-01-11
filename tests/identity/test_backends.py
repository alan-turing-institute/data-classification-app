from haven.identity.backends import CustomAzureOAuth2Backend


def test_returns_correct_fields():
    backend = CustomAzureOAuth2Backend()
    response = {
        "upn": "user1@dsg1",
        "mail": "user1@example.com",
        "name": "User One",
        "given_name": "User",
        "family_name": "One",
    }

    assert backend.get_user_details(response) == {
        "username": "user1@dsg1",
        "email": "user1@example.com",
        "fullname": "User One",
        "first_name": "User",
        "last_name": "One",
    }
