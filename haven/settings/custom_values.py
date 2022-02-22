from configurations import values

class DataBaseURLValueExtra(values.DatabaseURLValue):
    """Subclass in order to add atomic requests with a 
    keyword argument. Presumably could be further developed
    to include other db settings if necessary"""
    def __init__(self, *args, **kwargs):
        self.atomic = kwargs.pop("atomic", False)
        super().__init__(*args, **kwargs)

    def setup(self, name):
        value = super().setup(name)
        if self.atomic:
            value[self.alias]["ATOMIC_REQUESTS"] = True
        return value