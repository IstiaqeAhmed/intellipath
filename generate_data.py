import os
import django
import random
from django.utils import timezone
from datetime import timedelta

# ১. সবার আগে জ্যাঙ্গো সেটআপ (VS Code এটাকে এখানেই রাখবে)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intellipath.settings')
django.setup()


def generate_data():
    # ২. ফাংশনের ভেতরে ইমপোর্ট (VS Code এখন আর এগুলোকে উপরে সরাতে পারবে না!)
    from django.contrib.auth.models import User
    from students.models import Course, StudentProfile, Exam, ExamResult, Assignment, AssignmentSubmission, QuizResult

    print("ডেটা তৈরি শুরু হচ্ছে, দয়া করে অপেক্ষা করুন...")

    # ১. একটি ডামি কোর্স তৈরি
    course, created = Course.objects.get_or_create(
        title="Machine Learning for Beginners",
        defaults={'description': "This course is for ML Prediction."}
    )

    # ২. একটি ডামি এক্সাম তৈরি
    exam, created = Exam.objects.get_or_create(
        course=course,
        title="Final ML Evaluation",
        defaults={'total_marks': 100, 'pass_marks': 40}
    )

    # ৩. একটি ডামি অ্যাসাইনমেন্ট তৈরি
    assignment, created = Assignment.objects.get_or_create(
        course=course,
        title="Data Prediction Project",
        defaults={
            'description': "Submit your final ML project here.",
            'total_marks': 100,
            'deadline': timezone.now() + timedelta(days=7)
        }
    )

    # ৪. ১০০ জন স্টুডেন্ট এবং তাদের মার্কস তৈরি
    for i in range(1, 101):
        username = f"student_{i}"
        user, u_created = User.objects.get_or_create(
            username=username,
            defaults={'email': f"{username}@test.com"}
        )
        if u_created:
            user.set_password("pass12345")
            user.save()

        # প্রোফাইল তৈরি (Approved)
        StudentProfile.objects.get_or_create(
            user=user,
            defaults={
                'mobile_number': f"01700000{i:03d}",
                'transaction_id': f"TXN{i}999ML",
                'is_approved': True
            }
        )

        # বাস্তবসম্মত ডেটা তৈরির জন্য স্টুডেন্টদের ৩টি ক্যাটাগরিতে ভাগ করা
        profile_type = random.choice(['good', 'average', 'poor'])

        if profile_type == 'good':
            exam_score = random.randint(70, 100)
            assign_score = random.randint(75, 100)
            quiz_score = random.randint(8, 10)
        elif profile_type == 'average':
            exam_score = random.randint(40, 69)
            assign_score = random.randint(50, 74)
            quiz_score = random.randint(5, 7)
        else:  # poor / dropout chances
            exam_score = random.randint(10, 39)
            assign_score = random.randint(0, 49)
            quiz_score = random.randint(1, 4)

        # এক্সাম রেজাল্ট এন্ট্রি
        ExamResult.objects.get_or_create(
            student=user,
            exam=exam,
            defaults={
                'score': exam_score,
                'passed': exam_score >= exam.pass_marks
            }
        )

        # অ্যাসাইনমেন্ট রেজাল্ট এন্ট্রি
        AssignmentSubmission.objects.get_or_create(
            assignment=assignment,
            student=user,
            defaults={
                'marks_obtained': assign_score,
                'is_graded': True
            }
        )

        # কুইজ রেজাল্ট এন্ট্রি
        QuizResult.objects.get_or_create(
            user=user,
            topic="ML Basics Quiz",
            defaults={'score': f"{quiz_score}/10"}
        )

    print("✅ আলহামদুলিল্লাহ! ১০০ জন স্টুডেন্টের ডেটা সফলভাবে ক্লাউড ডাটাবেসে যুক্ত হয়েছে!")


# স্ক্রিপ্টটি রান করার কমান্ড
if __name__ == "__main__":
    generate_data()
