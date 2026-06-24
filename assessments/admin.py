from django.contrib import admin
from .models import *

admin.site.register(Questionnaire)
admin.site.register(Attribute)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(Response)
admin.site.register(Answer)
admin.site.register(Result)