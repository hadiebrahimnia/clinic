from django.contrib import admin
from .models import *

admin.site.register(Room)
admin.site.register(PsychologistNewPatients)
admin.site.register(WorkSchedule)
admin.site.register(Appointment)