from django.contrib import admin

from haven.projects import models

from django_otp.admin import OTPAdminSite
from django.contrib.auth.models import User
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.plugins.otp_totp.admin import TOTPDeviceAdmin

class OTPAdmin(OTPAdminSite):
    pass


admin_site = OTPAdmin(name='OTPAdmin')


admin.site.register(models.Project)
admin.site.register(models.Participant)
admin.site.register(models.ClassificationOpinion)
admin.site.register(models.ClassificationOpinionQuestion)
admin.site.register(models.WorkPackage)
admin_site.register(User)
admin_site.register(TOTPDevice, TOTPDeviceAdmin)
