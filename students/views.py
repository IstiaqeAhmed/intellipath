import json
import random
import google.generativeai as genai
from django.db.models import Count, Q, Sum
from django.contrib.auth.models import User
from pypdf import PdfReader

from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.http import JsonResponse

from intellipath.config import GOOGLE_API_KEY
from .forms import RegistrationForm, UserUpdateForm, ProfileUpdateForm
from .models import Course, CourseContent, StudentProgress, QuizResult, StudentProfile
from .models import Exam, ExamQuestion, ExamResult, Assignment, AssignmentSubmission, CreativeQuestion, ExamWrittenSubmission

# --- AI Setup ---
genai.configure(api_key=GOOGLE_API_KEY)


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    courses = Course.objects.all()
    return render(request, 'students/home.html', {'courses': courses})


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request, 'Registration successful! Please wait for admin approval.')
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'students/register.html', {'form': form})


# ==========================================
# 🎯 2026 ULTRA DASHBOARD (Courses + XP + Leaderboard)
# ==========================================
@login_required
def dashboard(request):
    # স্টুডেন্ট অ্যাপ্রুভড কিনা চেক করা
    if not hasattr(request.user, 'studentprofile') or not request.user.studentprofile.is_approved:
        messages.warning(
            request, 'আপনার অ্যাকাউন্টটি এখনো অ্যাডমিন দ্বারা অ্যাপ্রুভ করা হয়নি। দয়া করে অপেক্ষা করুন।')
        logout(request)
        return redirect('login')

    # ==========================================
    # 📚 ১. কোর্সের প্রগ্রেস হিসাব (Active Modules)
    # ==========================================
    courses = Course.objects.all()
    user_courses = []

    for course in courses:
        total_contents = course.contents.count()
        if total_contents > 0:
            completed_contents = StudentProgress.objects.filter(
                user=request.user,
                content__course=course,
                is_completed=True
            ).count()
            progress = int((completed_contents / total_contents) * 100)
        else:
            progress = 0

        user_courses.append({
            'course': course,
            'progress': progress
        })

    # ==========================================
    # 🧠 ২. বর্তমান ইউজারের মোট মার্কস (Total XP) হিসাব
    # ==========================================
    quiz_marks = 0
    for q in QuizResult.objects.filter(user=request.user):
        try:
            quiz_marks += int(q.score.split(' ')[0])
        except:
            pass

    exam_mcq = ExamResult.objects.filter(
        student=request.user).aggregate(Sum('score'))['score__sum'] or 0
    exam_cq = ExamWrittenSubmission.objects.filter(student=request.user, is_graded=True).aggregate(
        Sum('marks_obtained'))['marks_obtained__sum'] or 0
    assignment_marks = AssignmentSubmission.objects.filter(
        student=request.user, is_graded=True).aggregate(Sum('marks_obtained'))['marks_obtained__sum'] or 0

    total_xp = quiz_marks + exam_mcq + exam_cq + assignment_marks

    # ==========================================
    # 🏆 ৩. গ্লোবাল লিডারবোর্ড (Top 10 Cyber Ninjas)
    # ==========================================
    all_students = User.objects.filter(studentprofile__is_approved=True)
    leaderboard_data = []

    for std in all_students:
        q_m = 0
        for q in QuizResult.objects.filter(user=std):
            try:
                q_m += int(q.score.split(' ')[0])
            except:
                pass

        e_m = ExamResult.objects.filter(student=std).aggregate(
            Sum('score'))['score__sum'] or 0
        c_m = ExamWrittenSubmission.objects.filter(student=std, is_graded=True).aggregate(
            Sum('marks_obtained'))['marks_obtained__sum'] or 0
        a_m = AssignmentSubmission.objects.filter(student=std, is_graded=True).aggregate(
            Sum('marks_obtained'))['marks_obtained__sum'] or 0

        total = q_m + e_m + c_m + a_m
        if total > 0:  # যাদের অন্তত ১ মার্ক আছে, তারাই লিডারবোর্ডে আসবে
            leaderboard_data.append({'student': std, 'total': total})

    # সর্বোচ্চ মার্কস অনুযায়ী সাজানো (Top 10)
    leaderboard = sorted(
        leaderboard_data, key=lambda x: x['total'], reverse=True)[:10]

    # ইউজারের বর্তমান র‍্যাংক বের করা
    user_rank = "-"
    for index, data in enumerate(leaderboard):
        if data['student'] == request.user:
            user_rank = index + 1
            break

    # ==========================================
    # 🚀 ৪. অ্যাকটিভ এক্সাম এবং অ্যাসাইনমেন্ট
    # ==========================================
    exams = Exam.objects.all().order_by('-created_at')
    assignments = Assignment.objects.all().order_by('-deadline')

    context = {
        'user_courses': user_courses,  # কোর্স প্রগ্রেস
        'total_xp': total_xp,          # মোট মার্কস
        'user_rank': user_rank,        # র‍্যাংক
        'leaderboard': leaderboard,    # লিডারবোর্ড
        'exams': exams,                # এক্সাম
        'assignments': assignments,    # অ্যাসাইনমেন্ট
    }
    return render(request, 'students/dashboard.html', context)


@login_required
def course_content_detail(request, course_id, content_id=None):
    course = get_object_or_404(Course, id=course_id)
    contents = course.contents.all().order_by('order')

    if not contents.exists():
        messages.warning(
            request, "এই কোর্সে এখনো কোনো কন্টেন্ট আপলোড করা হয়নি।")
        return redirect('dashboard')

    if content_id:
        current_content = get_object_or_404(
            CourseContent, id=content_id, course=course)
    else:
        current_content = contents.first()

    if request.method == 'POST':
        progress_record, created = StudentProgress.objects.get_or_create(
            user=request.user,
            content=current_content
        )
        progress_record.is_completed = True
        progress_record.save()

        next_content = contents.filter(order__gt=current_content.order).first()
        if next_content:
            return redirect('course_content_detail', course_id=course.id, content_id=next_content.id)
        else:
            messages.success(
                request, f"অভিনন্দন! আপনি '{course.title}' কোর্সটি সফলভাবে শেষ করেছেন।")
            return redirect('dashboard')

    context = {
        'course': course,
        'contents': contents,
        'current_content': current_content,
    }
    return render(request, 'students/course_content.html', context)


def generate_quiz_from_text(text_content):
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""
        You are a strictly technical teacher. Create 5 multiple-choice questions based on the provided text.
        The questions and options MUST be written in Bengali (বাংলা) language.

        Rules:
        1. Output MUST be a valid JSON array.
        2. Do NOT use markdown code blocks (no ```json or ```).
        3. Keys must be exactly in English: "question", "options", "correct_answer".
        4. "options" must be a list of 4 strings (The string values MUST be in Bengali).
        5. "correct_answer" must be exactly one of the strings from "options" (in Bengali).

        Text content:
        {text_content[:3000]}
        """
        response = model.generate_content(prompt)
        cleaned_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(cleaned_text)
    except Exception as e:
        print(f"\n❌ Error generating quiz: {e}\n")
        return []


@login_required
def take_quiz(request, course_id, content_id):
    content = get_object_or_404(CourseContent, id=content_id)
    extracted_text = ""

    if content.content_type == 'pdf' and content.pdf_file:
        try:
            reader = PdfReader(content.pdf_file.path)
            for page in reader.pages:
                extracted_text += page.extract_text() + " "
        except Exception as e:
            extracted_text = content.title
    else:
        extracted_text = f"{content.title}. {content.body_text or ''}"

    if len(extracted_text.strip()) < 50:
        extracted_text = f"Generate general quiz questions about {content.title} in the context of {content.course.title}."

    session_key = f'quiz_data_{content.id}'

    if request.method == 'POST':
        user_answers = request.POST
        score = 0
        total = 0
        quiz_data = request.session.get(session_key, [])
        detailed_results = []

        for index, q in enumerate(quiz_data):
            total += 1
            selected_option = user_answers.get(f'question_{index}')
            is_correct = (selected_option == q['correct_answer'])

            if is_correct:
                score += 1

            detailed_results.append({
                'question': q['question'],
                'selected': selected_option,
                'correct': q['correct_answer'],
                'is_correct': is_correct
            })

        percentage = (score / total) * 100 if total > 0 else 0

        QuizResult.objects.create(
            user=request.user,
            topic=content.title,
            score=f"{score} / {total} ({round(percentage)}%)"
        )

        context = {
            'content': content,
            'score': score,
            'total': total,
            'percentage': round(percentage),
            'detailed_results': detailed_results,
        }
        return render(request, 'students/quiz_result.html', context)

    quiz_data = generate_quiz_from_text(extracted_text)
    request.session[session_key] = quiz_data

    return render(request, 'students/take_quiz.html', {'content': content, 'quiz_data': quiz_data})


@login_required
def ask_ai_tutor(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_question = data.get('question', '')

            if not user_question:
                return JsonResponse({'error': 'কোনো প্রশ্ন পাওয়া যায়নি।'}, status=400)

            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-2.5-flash')
            prompt = f"You are a helpful, friendly, and expert AI tutor for an online learning platform called IntelliPath. Answer the following student's question clearly, concisely, and accurately. Prefer answering in Bengali unless asked in English. Question: {user_question}"

            response = model.generate_content(prompt)
            return JsonResponse({'answer': response.text})

        except Exception as e:
            print(f"AI Tutor Error: {e}")
            return JsonResponse({'error': 'দুঃখিত, কোনো একটি সমস্যা হয়েছে। আবার চেষ্টা করুন।'}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(
            request.POST, request.FILES, instance=request.user.studentprofile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(
                request, f'আপনার প্রোফাইল সফলভাবে আপডেট করা হয়েছে!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.studentprofile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'students/profile.html', context)


@login_required
def course_certificate(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    course_contents = CourseContent.objects.filter(course=course)
    total_contents = course_contents.count()

    if total_contents == 0:
        messages.warning(
            request, '⚠️ এই কোর্সে এখনো কোনো কন্টেন্ট যুক্ত করা হয়নি!')
        return redirect('dashboard')

    completed_contents = StudentProgress.objects.filter(
        user=request.user,
        content__in=course_contents,
        is_completed=True
    ).count()

    progress_percentage = int((completed_contents / total_contents) * 100)

    if progress_percentage < 100:
        messages.warning(
            request, '⚠️ সার্টিফিকেট পেতে হলে আপনাকে আগে কোর্সটি ১০০% সম্পন্ন করতে হবে!')
        return redirect('dashboard')

    context = {
        'course': course,
    }
    return render(request, 'students/certificate.html', context)


# ==========================================
# 🚀 EXAM & ASSIGNMENT VIEWS (2026 EDITION)
# ==========================================
@login_required
def take_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    # স্টুডেন্ট আগে পরীক্ষা দিয়েছে কিনা চেক করা
    if ExamResult.objects.filter(student=request.user, exam=exam).exists() or ExamWrittenSubmission.objects.filter(student=request.user, exam=exam).exists():
        messages.warning(request, "আপনি ইতিমধ্যে এই পরীক্ষাটি দিয়েছেন!")
        return redirect('dashboard')

    if request.method == 'POST':
        # ১. MCQ এর মার্কস ক্যালকুলেশন
        score = 0
        for q in exam.questions.all():
            selected_option = request.POST.get(f'question_{q.id}')
            if selected_option == q.correct_option:
                score += 1  # প্রতিটি সঠিক উত্তরের জন্য ১ মার্ক

        # MCQ রেজাল্ট সেভ করা
        if exam.questions.exists():
            ExamResult.objects.create(
                student=request.user,
                exam=exam,
                score=score,
                passed=(score >= exam.pass_marks)
            )

        # ২. CQ (সৃজনশীল) খাতা আপলোড হ্যান্ডেল করা
        if 'cq_answer_file' in request.FILES:
            ExamWrittenSubmission.objects.create(
                student=request.user,
                exam=exam,
                answer_file=request.FILES['cq_answer_file']
            )

        messages.success(
            request, "আপনার পরীক্ষা সফলভাবে জমা হয়েছে! অ্যাডমিন খাতা দেখার পর ড্যাশবোর্ডে মার্কস যোগ হবে।")
        return redirect('dashboard')

    return render(request, 'students/take_exam.html', {'exam': exam})


@login_required
def submit_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)

    # স্টুডেন্ট আগে জমা দিয়েছে কিনা চেক করা
    if AssignmentSubmission.objects.filter(student=request.user, assignment=assignment).exists():
        messages.warning(
            request, "আপনি ইতিমধ্যে এই অ্যাসাইনমেন্টটি জমা দিয়েছেন!")
        return redirect('dashboard')

    if request.method == 'POST':
        if 'submitted_file' in request.FILES:
            AssignmentSubmission.objects.create(
                assignment=assignment,
                student=request.user,
                submitted_file=request.FILES['submitted_file']
            )
            messages.success(
                request, "আপনার অ্যাসাইনমেন্ট সফলভাবে জমা হয়েছে!")
            return redirect('dashboard')

    return render(request, 'students/submit_assignment.html', {'assignment': assignment})
