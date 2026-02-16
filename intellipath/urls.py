"""
URL configuration for intellipath project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include  # <--- ১. include যোগ করুন

from students import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # ২. এই লাইনটি যোগ করুন (লগইন সিস্টেমের জন্য)
    path('accounts/', include('django.contrib.auth.urls')),

    path('', views.dashboard, name='home'),
    # নতুন লাইনটি যোগ করুন:
    path('quiz/', views.generate_quiz, name='quiz'),
    path('course/<int:course_id>/', views.course_content, name='course_content'),
]
