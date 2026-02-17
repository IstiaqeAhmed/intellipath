from django.db import models
# এই লাইনটি ফাইলের একদম ওপরে থাকতে হবে
from django.contrib.auth.models import User

# আমাদের কোর্সের জন্য একটি টেবিল


class Course(models.Model):
    title = models.CharField(max_length=200)  # কোর্সের নাম
    description = models.TextField()           # কোর্সের বিবরণ
    # ইউটিউব ভিডিওর আইডি (যেমন: dQw4w9WgXcQ)
    video_id = models.CharField(max_length=50, null=True, blank=True)
    progress = models.IntegerField(default=0)  # কতটুকু শেষ হয়েছে (0-100)

    def __str__(self):
        return self.title  # অ্যাডমিন প্যানেলে নাম দেখানোর জন্য

# নতুন ক্লাসটি এভাবে লিখুন (ইনডেন্টেশন খেয়াল করুন)


class QuizResult(models.Model):
    user = models.ForeignKey(
        'auth.User', on_delete=models.CASCADE)  # ৪টি স্পেস ডানে
    # ৪টি স্পেস ডানে
    topic = models.CharField(max_length=200)
    score = models.CharField(max_length=50, null=True,
                             blank=True)   # ৪টি স্পেস ডানে
    date = models.DateTimeField(
        auto_now_add=True)                  # ৪টি স্পেস ডানে

    def __str__(self):
        return f"{self.user.username} - {self.topic}"
    # ==========================================
# 👇 এখান থেকে নতুন কোড (Registration & Payment)
# ==========================================


class StudentProfile(models.Model):
    # প্রতিটি ইউজারের সাথে এটি লিংক করা থাকবে
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # রেজিস্ট্রেশন তথ্য
    mobile_number = models.CharField(max_length=15)  # মোবাইল নম্বর (বিকাশ/নগদ)
    transaction_id = models.CharField(max_length=50)  # পেমেন্ট TrxID

    # পেমেন্ট স্ট্যাটাস (ডিফল্টভাবে False থাকবে, অ্যাডমিন True করলে লগইন হবে)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.mobile_number}"
