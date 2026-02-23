from django.contrib import admin
from .models import Course, CourseContent, StudentProgress, StudentProfile, QuizResult
# নতুন CQ এবং Written Submission মডেলগুলো ইম্পোর্ট করা হলো
from .models import Exam, ExamQuestion, ExamResult, Assignment, AssignmentSubmission, CreativeQuestion, ExamWrittenSubmission

# কোর্সের ভেতরেই যাতে কন্টেন্ট যোগ করা যায় তার ব্যবস্থা


class ContentInline(admin.TabularInline):
    model = CourseContent
    extra = 1


class CourseAdmin(admin.ModelAdmin):
    inlines = [ContentInline]


# এডমিন প্যানেলে রেজিস্ট্রেশন (register) করা
admin.site.register(Course, CourseAdmin)
admin.site.register(CourseContent)
admin.site.register(StudentProgress)
admin.site.register(QuizResult)

# স্টুডেন্ট অ্যাপ্রুভাল সিস্টেম


class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'mobile_number', 'transaction_id', 'is_approved')
    list_editable = ('is_approved',)


admin.site.register(StudentProfile, StudentProfileAdmin)

# ==========================================
# 🚀 EXAM, MCQ, CQ & ASSIGNMENT ADMIN SECTION
# ==========================================

# MCQ Question Box


class ExamQuestionInline(admin.StackedInline):
    model = ExamQuestion
    extra = 1

# CQ (সৃজনশীল) Question Box


class CreativeQuestionInline(admin.StackedInline):
    model = CreativeQuestion
    extra = 1


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'total_marks')
    # এখানে MCQ এবং CQ দুই ধরনের প্রশ্ন দেওয়ার অপশন একসাথে অ্যাড করা হলো
    inlines = [ExamQuestionInline, CreativeQuestionInline]


@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'score', 'passed', 'date_taken')
    list_filter = ('passed', 'exam')

# স্টুডেন্টদের লিখিত খাতা (CQ) দেখার জন্য


@admin.register(ExamWrittenSubmission)
class ExamWrittenSubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'answer_file',
                    'marks_obtained', 'is_graded')
    # বাইরে থেকেই মার্কস এডিট করার ম্যাজিক!
    list_editable = ('marks_obtained', 'is_graded')
    list_filter = ('is_graded', 'exam')


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'deadline', 'total_marks')


# অ্যাসাইনমেন্টের খাতা দেখার জন্য
@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'assignment', 'submitted_file',
                    'marks_obtained', 'is_graded')
    # বাইরে থেকেই মার্কস এডিট করার ম্যাজিক!
    list_editable = ('marks_obtained', 'is_graded')
    list_filter = ('is_graded',)
    search_fields = ('student__username', 'assignment__title')
