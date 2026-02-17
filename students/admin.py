from django.contrib import admin
from .models import Course, QuizResult, StudentProfile

admin.site.register(Course)
admin.site.register(QuizResult)

# StudentProfile দেখার জন্য বিশেষ ব্যবস্থা


class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'mobile_number', 'transaction_id', 'is_approved')
    list_editable = ('is_approved',)  # এখান থেকেই টিক দিয়ে অ্যাপ্রুভ করা যাবে


admin.site.register(StudentProfile, StudentProfileAdmin)
