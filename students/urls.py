from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # ড্যাশবোর্ড এবং হোমপেজ
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # অথেনটিকেশন এবং রেজিস্ট্রেশন
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='students/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    # কোর্স এবং কুইজ (যদি এগুলো views.py তে থাকে)
    path('course/<int:course_id>/', views.course_content, name='course_content'),
    # path('quiz/', views.quiz_view, name='quiz'),  # যদি quiz_view না থাকে তবে এই লাইনের শুরুতে # দিয়ে কমেন্ট করে রাখুন
]
