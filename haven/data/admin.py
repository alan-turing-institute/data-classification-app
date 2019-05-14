from django.contrib import admin

from .models import ClassificationQuestion, Dataset


admin.site.register(ClassificationQuestion)
admin.site.register(Dataset)
