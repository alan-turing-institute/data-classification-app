from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import ClassificationQuestion, Dataset


admin.site.register(ClassificationQuestion, SimpleHistoryAdmin)
admin.site.register(Dataset)
