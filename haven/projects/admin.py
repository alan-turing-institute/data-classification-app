from django.contrib import admin

from haven.projects import models


admin.site.register(models.Project)
admin.site.register(models.Participant)
admin.site.register(models.ClassificationOpinion)
admin.site.register(models.ClassificationOpinionQuestion)
admin.site.register(models.WorkPackage)
