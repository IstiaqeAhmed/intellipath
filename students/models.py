from django.db import models

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
