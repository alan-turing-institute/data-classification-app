import environ

env = environ.Env()

def add_backend(BACKENDS, NAMES, exclusive=False):
    if exclusive:
        BACKENDS = []
    BACKENDS.extend(["social_core.backends.github.GithubOAuth2"])
    NAMES['github'] = "GitHub"
    return BACKENDS, NAMES

SOCIAL_AUTH_GITHUB_KEY = env.str("GITHUB_OAUTH2_KEY", default="")
SOCIAL_AUTH_GITHUB_SECRET = env.str("GITHUB_OAUTH2_SECRET", default="")