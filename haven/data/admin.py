from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from haven.data.models import (
    ClassificationGuidance,
    ClassificationQuestion,
    Dataset,
)


admin.site.register(ClassificationGuidance)
admin.site.register(ClassificationQuestion, SimpleHistoryAdmin)
admin.site.register(Dataset)
