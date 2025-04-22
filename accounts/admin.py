from django.contrib import admin

# Register your models here.
from .models import AttendanceRecord, Course, StudentProfile

admin.site.register(AttendanceRecord)
admin.site.register(Course)
admin.site.register(StudentProfile)