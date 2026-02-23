from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ১. অ্যাডমিন প্যানেল
    path('admin/', admin.site.urls),

    # ২. স্টুডেন্ট অ্যাপের লিংক (সরাসরি আপনার বানানো ডিজাইন কাজ করবে)
    path('', include('students.urls')),
]

# ছবি এবং পিডিএফ ফাইল সার্ভ করার জন্য
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
