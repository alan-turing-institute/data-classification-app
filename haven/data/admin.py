from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path
from simple_history.admin import SimpleHistoryAdmin

from haven.data.models import ClassificationGuidance, ClassificationQuestion, Dataset


class ClassificationQuestionAdmin(SimpleHistoryAdmin):
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('<int:pk>/flowchart/', self.admin_site.admin_view(self.flowchart), name='flowchart')
        ]
        return my_urls + urls

    def flowchart(self, request, pk=None):
        question = ClassificationQuestion.objects.get(pk=pk)
        questions = set()
        tiers = set()
        edges = set()

        def add_question(q):
            if q in questions:
                return
            questions.add(q)
            if q.yes_tier is not None:
                tiers.add(q.yes_tier)
                edges.add((q.name, q.yes_tier, "Yes"))
            if q.no_tier is not None:
                tiers.add(q.no_tier)
                edges.add((q.name, q.no_tier, "No"))
            if q.yes_question is not None:
                add_question(q.yes_question)
                edges.add((q.name, q.yes_question.name, "Yes"))
            if q.no_question is not None:
                add_question(q.no_question)
                edges.add((q.name, q.no_question.name, "No"))
        add_question(question)

        context = dict(
           # Include common variables for rendering the admin template.
           self.admin_site.each_context(request),
           object=question,
           opts=self.model._meta,
           questions=questions,
           tiers=tiers,
           edges=edges,
        )
        return TemplateResponse(request, "admin/data/classificationquestion/flowchart.html", context)


admin.site.register(ClassificationGuidance)
admin.site.register(ClassificationQuestion, ClassificationQuestionAdmin)
admin.site.register(Dataset)
