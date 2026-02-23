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

    # 🚀 ম্যাজিক ট্র্যাপ: কেউ ভুল করে accounts/login/ এ গেলেও আমাদের সুন্দর পেজেই আসবে!
    path('accounts/login/',
         auth_views.LoginView.as_view(template_name='students/login.html')),

    # 🎯 ১০০% সিকিউরড POST লগআউট
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    # কোর্স এবং কন্টেন্ট
    path('course/<int:course_id>/',
         views.course_content_detail, name='course_content'),
    path('course/<int:course_id>/<int:content_id>/',
         views.course_content_detail, name='course_content_detail'),

    # কুইজ এবং AI টিউটর
    path('course/<int:course_id>/content/<int:content_id>/quiz/',
         views.take_quiz, name='take_quiz'),
    path('ask-ai/', views.ask_ai_tutor, name='ask_ai_tutor'),

    # প্রোফাইল ও সার্টিফিকেট
    path('profile/', views.profile, name='profile'),
    path('course/<int:course_id>/certificate/',
         views.course_certificate, name='course_certificate'),

    # এক্সাম ও অ্যাসাইনমেন্ট
    path('exam/<int:exam_id>/', views.take_exam, name='take_exam'),
    path('assignment/<int:assignment_id>/',
         views.submit_assignment, name='submit_assignment'),
]
