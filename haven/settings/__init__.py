from .auth_mixins import (
    LocalUserMixin,
    RemoteUserMixin,
    GitHubUserMixin,
    ORCIDSandboxUserMixin,
    AzureUserMixin
)

from .environments import (
    Local, Development, Test, Production
)

class GitHubUserLocal(GitHubUserMixin, Local):
    pass

class GitHubORCIDUserLocal(GitHubUserMixin, ORCIDSandboxUserMixin, Local):
    pass

class GitHubUserProduction(GitHubUserMixin, Production):
    pass

class RemoteUserProduction(RemoteUserMixin, Production):
    pass

class AzureUserProduction(AzureUserMixin, Production):
    pass
