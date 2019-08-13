from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import ClassificationGuidance, ClassificationQuestion, Dataset


admin.site.register(ClassificationGuidance)
admin.site.register(ClassificationQuestion, SimpleHistoryAdmin)
admin.site.register(Dataset)
