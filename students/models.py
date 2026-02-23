from django.db import models
from django.contrib.auth.models import User

# ১. কোর্সের নাম ও বিবরণ


class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    thumbnail = models.ImageField(
        upload_to='thumbnails/', null=True, blank=True)

    def __str__(self):
        return self.title

# ২. কোর্সের কন্টেন্ট (ভিডিও, পিডিএফ, টেক্সট)


# ২. কোর্সের কন্টেন্ট (ভিডিও, পিডিএফ, টেক্সট)
class CourseContent(models.Model):
    CONTENT_TYPES = (
        ('video', 'Video'),
        ('pdf', 'PDF'),
        ('text', 'Article/Text'),
    )

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='contents')
    title = models.CharField(max_length=200)
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES)

    # ভিডিও হলে ইউটিউব আইডি, পিডিএফ হলে ফাইল, টেক্সট হলে লেখা
    video_id = models.CharField(
        max_length=50, null=True, blank=True, help_text="Only for YouTube Video ID")

    # 👇 🎯 শুধু এই নতুন লাইনটি যোগ করা হয়েছে (নিজস্ব ভিডিও আপলোডের জন্য) 👇
    video_file = models.FileField(
        upload_to='course_videos/', null=True, blank=True, help_text="Upload .mp4 video files here")

    pdf_file = models.FileField(upload_to='pdfs/', null=True, blank=True)
    body_text = models.TextField(
        null=True, blank=True, help_text="Text for AI to generate quiz from")

    order = models.IntegerField(default=1)  # সিরিয়াল মেইনটেইন করার জন্য

    def __str__(self):
        return f"{self.course.title} - {self.title}"

# ৩. প্রগ্রেস ট্র্যাকিং (কে কতটুকু শেষ করল)


class StudentProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.ForeignKey(CourseContent, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    completion_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.content.title}"

# ৪. ইউজারের প্রোফাইল (রেজিস্ট্রেশন ও পেমেন্ট)


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mobile_number = models.CharField(max_length=15)
    transaction_id = models.CharField(max_length=50)
    is_approved = models.BooleanField(default=False)
    # 👇 শুধু এই নতুন লাইনটি যোগ করুন 👇
    profile_picture = models.ImageField(
        upload_to='profile_pics/', default='profile_pics/default.png', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.mobile_number}"

# ৫. কুইজ রেজাল্ট


class QuizResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.CharField(max_length=200)
    score = models.CharField(max_length=50, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.topic}"

# ==========================================
# 🚀 ULTRA MAX PRO FEATURES: EXAM & ASSIGNMENT
# ==========================================


class Exam(models.Model):
    course = models.ForeignKey(
        'Course', on_delete=models.CASCADE, related_name='exams')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    total_marks = models.IntegerField(default=100)
    pass_marks = models.IntegerField(default=40)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class ExamQuestion(models.Model):
    exam = models.ForeignKey(
        Exam, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)

    CORRECT_OPTIONS = (
        ('A', 'Option A'),
        ('B', 'Option B'),
        ('C', 'Option C'),
        ('D', 'Option D'),
    )
    correct_option = models.CharField(max_length=1, choices=CORRECT_OPTIONS)

    def __str__(self):
        return self.question_text[:50]


class ExamResult(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    passed = models.BooleanField(default=False)
    date_taken = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.exam.title} - {self.score}"


class Assignment(models.Model):
    course = models.ForeignKey(
        'Course', on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=255)
    description = models.TextField()
    attachment = models.FileField(
        upload_to='assignments/questions/', blank=True, null=True)
    total_marks = models.IntegerField(default=100)
    deadline = models.DateTimeField()

    def __str__(self):
        return self.title


class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    submitted_file = models.FileField(upload_to='assignments/submissions/')
    submitted_at = models.DateTimeField(auto_now_add=True)
    marks_obtained = models.IntegerField(default=0, blank=True, null=True)
    is_graded = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.username} - {self.assignment.title}"
# ==========================================
# 📝 EXAM CQ (সৃজনশীল প্রশ্ন) এবং খাতা জমা
# ==========================================


class CreativeQuestion(models.Model):
    exam = models.ForeignKey(
        Exam, on_delete=models.CASCADE, related_name='cq_questions')
    stimulus = models.TextField(help_text="উদ্দীপক বা অনুচ্ছেদ লিখুন")

    question_k = models.CharField(
        max_length=500, help_text="ক - জ্ঞানমূলক (১ মার্ক)")
    question_kh = models.CharField(
        max_length=500, help_text="খ - অনুধাবনমূলক (২ মার্ক)")
    question_g = models.CharField(
        max_length=500, help_text="গ - প্রয়োগমূলক (৩ মার্ক)")
    question_gh = models.CharField(
        max_length=500, help_text="ঘ - উচ্চতর দক্ষতামূলক (৪ মার্ক)")

    def __str__(self):
        return f"{self.exam.title} - CQ Question"


class ExamWrittenSubmission(models.Model):
    exam = models.ForeignKey(
        Exam, on_delete=models.CASCADE, related_name='written_submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    answer_file = models.FileField(
        upload_to='exams/cq_answers/', help_text="স্টুডেন্ট তার খাতায় লেখা উত্তরের ছবি বা PDF আপলোড করবে")
    marks_obtained = models.IntegerField(default=0, blank=True, null=True)
    is_graded = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.exam.title} Written Script"
