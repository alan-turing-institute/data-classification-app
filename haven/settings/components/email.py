import environ

env = environ.Env()

# EMAIL
# ------------------------------------------------------------------------------
EMAIL_HOST = env.str("EMAIL_HOST", default="")
if EMAIL_HOST:
    EMAIL_HOST_USER = env.str("EMAIL_HOST_USER", default="")
    EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD", default="")
    EMAIL_PORT = env.int("EMAIL_PORT", default=587)
    EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)

DEFAULT_FROM_MAIL = env.str("FROM_MAIL", default="noreply@dsgroupdev.co.uk")