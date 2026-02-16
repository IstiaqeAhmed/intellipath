from django.contrib import admin
from .models import Course  # আমাদের মডেল ইমপোর্ট করলাম

admin.site.register(Course)  # অ্যাডমিন প্যানেলে যুক্ত করলাম
