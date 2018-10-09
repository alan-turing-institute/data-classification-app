from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Participant, User


admin.site.register(User, UserAdmin)
admin.site.register(Participant)
