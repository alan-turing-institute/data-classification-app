from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from haven.data.models import (
    ClassificationGuidance,
    ClassificationQuestion,
    ClassificationQuestionSet,
    Dataset,
)


class ClassificationQuestionAdmin(SimpleHistoryAdmin):
    autocomplete_fields = ["yes_question", "no_question"]
    search_fields = ["question_set__name", "question", "name"]


admin.site.register(ClassificationGuidance)
admin.site.register(ClassificationQuestion, ClassificationQuestionAdmin)
admin.site.register(ClassificationQuestionSet)
admin.site.register(Dataset)
