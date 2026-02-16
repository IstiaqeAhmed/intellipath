from .models import Course, QuizResult  # QuizResult ইমপোর্ট করুন
from django.contrib.auth.decorators import login_required
from intellipath.config import GOOGLE_API_KEY
from django.shortcuts import render
from .models import Course
import google.generativeai as genai

genai.configure(api_key=GOOGLE_API_KEY)


# ফাইলের শুরুতে import এবং API Key যেমন ছিল তেমনই থাকবে...

# --- এই নতুন ফাংশনটি ফাইলের শেষে যোগ করুন ---


def generate_quiz(request):
    quiz_content = None
    topic = None

    if request.method == 'POST':
        topic = request.POST.get('topic')
        if topic:
            try:
                genai.configure(api_key=GOOGLE_API_KEY)
                model = genai.GenerativeModel('gemini-2.5-flash')
                prompt = f"Create a short quiz with 3 MCQs about '{topic}'. Show correct answers at the end."
                response = model.generate_content(prompt)
                quiz_content = response.text

                # ম্যাজিক: কুইজটি ডাটাবেসে সেভ করা হচ্ছে
                if request.user.is_authenticated:
                    QuizResult.objects.create(
                        user=request.user,
                        topic=topic,
                        score="Completed"  # আপাতত আমরা কমপ্লিটেড রাখছি
                    )
            except Exception as e:
                quiz_content = f"Error: {e}"

    return render(request, 'students/quiz.html', {'quiz_content': quiz_content, 'topic': topic})


@login_required(login_url='login')  # <--- এই লাইনটি যোগ করুন
# আপনার বাকি কোড...
def dashboard(request):
    courses = Course.objects.all()

    # ১. কুইজ হিস্ট্রি নিয়ে আসা
    quiz_history = []
    if request.user.is_authenticated:
        quiz_history = QuizResult.objects.filter(
            user=request.user).order_by('-date')

    # ২. AI চ্যাটবটের জন্য ভেরিয়েবল ডিফাইন করা (এরর সমাধান)
    ai_response = None

    # ৩. চ্যাটবট লজিক
    if request.method == 'POST':
        user_question = request.POST.get('question')
        if user_question:
            try:
                genai.configure(api_key=GOOGLE_API_KEY)
                # আপনার লিস্ট অনুযায়ী লেটেস্ট মডেল ব্যবহার করছি
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(user_question)
                ai_response = response.text
            except Exception as e:
                ai_response = f"দুঃখিত, সমস্যা হয়েছে: {e}"

    # ৪. সব ডেটা টেমপ্লেটে পাঠানো
    context = {
        'courses': courses,
        'quiz_history': quiz_history,
        'ai_response': ai_response
    }
    return render(request, 'students/dashboard.html', context)


def course_content(request, course_id):
    # আইডি অনুযায়ী নির্দিষ্ট কোর্সটি খুঁজে বের করা
    course = Course.objects.get(id=course_id)
    return render(request, 'students/course_content.html', {'course': course})
