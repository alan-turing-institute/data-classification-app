import environ

env = environ.Env()

AUTHENTICATION_BACKEND = "social_core.backends.github.GithubOAuth2"
AUTH_DISPLAY_NAME = "GitHub"

SOCIAL_AUTH_GITHUB_KEY = env.str("GITHUB_OAUTH2_KEY", default="")
SOCIAL_AUTH_GITHUB_SECRET = env.str("GITHUB_OAUTH2_SECRET", default="")