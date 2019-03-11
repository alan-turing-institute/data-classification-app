from django.contrib import admin

from .models import ClassificationOpinion, Participant, Project


admin.site.register(Project)
admin.site.register(Participant)
admin.site.register(ClassificationOpinion)
