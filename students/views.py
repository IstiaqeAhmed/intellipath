from django.shortcuts import get_object_or_404, redirect
import os
from .models import ExamResult, AssignmentSubmission, QuizResult
from django.shortcuts import render, get_object_or_404
import pickle
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
from .models import Exam, ExamQuestion, ExamResult, Assignment, Quiz, QuizQuestion, ManualQuizSubmission, AssignmentSubmission, CreativeQuestion, ExamWrittenSubmission

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
@login_required
@login_required
def dashboard(request):
    if not hasattr(request.user, 'studentprofile') or not request.user.studentprofile.is_approved:
        messages.warning(
            request, 'আপনার অ্যাকাউন্টটি এখনো অ্যাডমিন দ্বারা অ্যাপ্রুভ করা হয়নি। দয়া করে অপেক্ষা করুন।')
        logout(request)
        return redirect('login')

    # ==========================================
    # 📚 ১. কোর্সের প্রগ্রেস হিসাব
    # ==========================================
    courses = Course.objects.prefetch_related('contents')
    user_progresses = StudentProgress.objects.filter(
        user=request.user, is_completed=True)
    completed_counts = {}
    for p in user_progresses:
        course_id = p.content.course_id
        completed_counts[course_id] = completed_counts.get(course_id, 0) + 1

    user_courses = []
    for course in courses:
        total_contents = course.contents.count()
        progress = int((completed_counts.get(course.id, 0) /
                       total_contents) * 100) if total_contents > 0 else 0
        user_courses.append({'course': course, 'progress': progress})

    # ==========================================
    # 🏆 ২. গ্লোবাল লিডারবোর্ড ও মোট মার্কস
    # ==========================================
    all_students = User.objects.filter(
        studentprofile__is_approved=True).select_related('studentprofile')

    all_exams = ExamResult.objects.all()
    all_cqs = ExamWrittenSubmission.objects.filter(is_graded=True)
    all_assigns = AssignmentSubmission.objects.filter(is_graded=True)
    # 🚀 নতুন ম্যানুয়াল কুইজ রেজাল্ট
    all_manual_quizzes = ManualQuizSubmission.objects.all()

    student_scores = {std.id: 0 for std in all_students}

    # এক্সাম, অ্যাসাইনমেন্ট এবং অফিসিয়াল কুইজের মার্কস যোগ করা (AI প্র্যাকটিস কুইজ বাদ)
    for e in all_exams:
        if e.student_id in student_scores:
            student_scores[e.student_id] += e.score
    for c in all_cqs:
        if c.student_id in student_scores:
            student_scores[c.student_id] += c.marks_obtained
    for a in all_assigns:
        if a.student_id in student_scores:
            student_scores[a.student_id] += a.marks_obtained
    for mq in all_manual_quizzes:
        if mq.student_id in student_scores:
            student_scores[mq.student_id] += mq.score_obtained

    leaderboard_data = [{'student': std, 'total': student_scores[std.id]}
                        for std in all_students if student_scores[std.id] > 0]
    leaderboard = sorted(
        leaderboard_data, key=lambda x: x['total'], reverse=True)[:10]

    total_xp = student_scores.get(request.user.id, 0)
    total_xp = int(round(float(total_xp)))
    user_rank = "-"
    for index, data in enumerate(leaderboard):
        if data['student'] == request.user:
            user_rank = index + 1
            break

    # ==========================================
    # 🚀 ৩. অ্যাকটিভ এক্সাম, অ্যাসাইনমেন্ট এবং কুইজ
    # ==========================================
    exams = Exam.objects.all().order_by('-created_at')
    assignments = Assignment.objects.all().order_by('-deadline')
    quizzes = Quiz.objects.all().order_by('-created_at')

    submitted_exams = list(ExamResult.objects.filter(
        student=request.user).values_list('exam_id', flat=True))
    submitted_cqs = list(ExamWrittenSubmission.objects.filter(
        student=request.user).values_list('exam_id', flat=True))
    submitted_exam_ids = submitted_exams + submitted_cqs
    submitted_assignment_ids = list(AssignmentSubmission.objects.filter(
        student=request.user).values_list('assignment_id', flat=True))
    submitted_quiz_ids = list(ManualQuizSubmission.objects.filter(
        # 🚀 কোন কুইজ দেওয়া হয়েছে তার লিস্ট
        student=request.user).values_list('quiz_id', flat=True))

    context = {
        'user_courses': user_courses, 'total_xp': total_xp, 'user_rank': user_rank,
        'leaderboard': leaderboard, 'exams': exams, 'assignments': assignments, 'quizzes': quizzes,
        'submitted_exam_ids': submitted_exam_ids, 'submitted_assignment_ids': submitted_assignment_ids,
        'submitted_quiz_ids': submitted_quiz_ids,  # 🚀 ড্যাশবোর্ডে পাঠানো হলো
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
            return JsonResponse({'error': 'AI মেন্টর এই মুহূর্তে অনেক বেশি রিকোয়েস্ট পাচ্ছে। অনুগ্রহ করে ১ মিনিট পর আবার প্রশ্ন করুন।'}, status=500)

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


# আমাদের ট্রেইন করা ML মডেলটি লোড করা
MODEL_PATH = os.path.join(settings.BASE_DIR, 'student_predictor_model.pkl')
with open(MODEL_PATH, 'rb') as f:
    ml_model = pickle.load(f)


def predict_student(request, user_id):
    # স্টুডেন্টকে ডাটাবেস থেকে খুঁজে বের করা
    student = get_object_or_404(User, id=user_id)

    # স্টুডেন্টের মার্কসগুলো সংগ্রহ করা
    exam_result = ExamResult.objects.filter(student=student).first()
    exam_score = exam_result.score if exam_result else 0

    assign_sub = AssignmentSubmission.objects.filter(student=student).first()
    assign_score = assign_sub.marks_obtained if assign_sub else 0

    # কুইজ স্কোরের নতুন অপ্টিমাইজড লজিক
    # কুইজ স্কোরের নতুন লজিক (সবগুলো কুইজের মার্কস যোগ করবে)
    quiz_results = QuizResult.objects.filter(user=student)
    quiz_score = 0
    for q in quiz_results:
        score_str = str(q.score).strip()
        try:
            # "7 / 10 (70%)" অথবা "7/10" অথবা "7" যেভাবেই থাকুক, শুধু প্রাপ্ত নম্বরটা যোগ করবে
            if '/' in score_str:
                quiz_score += int(score_str.split('/')[0].strip())
            else:
                quiz_score += int(score_str.split()[0].strip())
        except ValueError:
            pass

    # মডেল দিয়ে প্রেডিক্ট করা (পাস নাকি ফেল)
    prediction = ml_model.predict([[exam_score, assign_score, quiz_score]])[0]

    if prediction == 1:
        status = "Pass (সফলভাবে কোর্স শেষ করবে) ✅"
        color = "green"
    else:
        status = "Dropout (ঝরে পড়ার সম্ভাবনা আছে) ⚠️"
        color = "red"

    context = {
        'student': student,
        'exam_score': exam_score,
        'assign_score': assign_score,
        'quiz_score': quiz_score,
        'status': status,
        'color': color
    }

    return render(request, 'prediction_result.html', context)


def teacher_dashboard(request):
    from django.contrib.auth.models import User
    # 🚀 QuizResult বাদ দিয়ে ManualQuizSubmission আনা হলো (স্টুডেন্ট ড্যাশবোর্ডের মতো)
    from .models import ExamResult, ExamWrittenSubmission, AssignmentSubmission, ManualQuizSubmission

    students = User.objects.filter(is_superuser=False)

    # ডিকশনারি তৈরি করে ফাস্ট ক্যালকুলেশনের জন্য ডেটা জিরো (0) করে রাখা হলো
    student_scores = {std.id: {'exam': 0, 'assign': 0,
                               'quiz': 0, 'total': 0} for std in students}

    # ১. এক্সাম মার্কস (MCQ + CQ)
    for e in ExamResult.objects.all():
        if e.student_id in student_scores:
            student_scores[e.student_id]['exam'] += e.score
            student_scores[e.student_id]['total'] += e.score

    for c in ExamWrittenSubmission.objects.filter(is_graded=True):
        if c.student_id in student_scores:
            student_scores[c.student_id]['exam'] += c.marks_obtained
            student_scores[c.student_id]['total'] += c.marks_obtained

    # ২. অ্যাসাইনমেন্ট মার্কস
    for a in AssignmentSubmission.objects.filter(is_graded=True):
        if a.student_id in student_scores:
            student_scores[a.student_id]['assign'] += a.marks_obtained
            student_scores[a.student_id]['total'] += a.marks_obtained

    # ৩. অফিসিয়াল কুইজ মার্কস (AI কুইজ বাদ!)
    for mq in ManualQuizSubmission.objects.all():
        if mq.student_id in student_scores:
            student_scores[mq.student_id]['quiz'] += mq.score_obtained
            student_scores[mq.student_id]['total'] += mq.score_obtained

    student_data = []

    # ৪. ডাটাবেসে রিকোয়েস্ট না পাঠিয়ে মেমোরি থেকে ডেটা সাজানো
    for student in students:
        # দশমিক (Float) এড়ানোর জন্য int(round()) ব্যবহার করা হয়েছে
        student_data.append({
            'id': student.id,
            'username': student.username,
            'exam_score': int(round(student_scores[student.id]['exam'])),
            'assign_score': int(round(student_scores[student.id]['assign'])),
            'quiz_score': int(round(student_scores[student.id]['quiz'])),
            'total_score': int(round(student_scores[student.id]['total'])),
        })

    # টোটাল স্কোরের ভিত্তিতে বড় থেকে ছোট সাজানো (যাতে টপাররা ওপরে থাকে)
    student_data = sorted(
        student_data, key=lambda x: x['total_score'], reverse=True)

    return render(request, 'teacher_dashboard.html', {'students': student_data})


@login_required
def take_manual_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    # 🛑 চেক করা হচ্ছে স্টুডেন্ট আগেই কুইজ দিয়েছে কি না
    if ManualQuizSubmission.objects.filter(student=request.user, quiz=quiz).exists():
        messages.warning(
            request, 'আপনি ইতোমধ্যে এই কুইজটি দিয়েছেন! একবারের বেশি দেওয়া যাবে না।')
        return redirect('dashboard')

    questions = QuizQuestion.objects.filter(quiz=quiz)

    if request.method == 'POST':
        correct_answers = 0
        total_questions = questions.count()

        for q in questions:
            selected_option = request.POST.get(f'question_{q.id}')
            if selected_option == q.correct_option:
                correct_answers += 1

        # 🎯 মার্কস কনভার্ট করা (যেমন: ২ টা প্রশ্নে সঠিক হলে এবং মোট মার্কস ১০ হলে (২/২)*১০ = ১০ পাবে)
       # 🎯 মার্কস কনভার্ট করা
    scaled_score = (correct_answers / total_questions) * \
        quiz.total_marks if total_questions > 0 else 0

    # 💾 রেজাল্ট ডাটাবেসে সেভ করা
    ManualQuizSubmission.objects.create(
        student=request.user, quiz=quiz, score_obtained=scaled_score)

    messages.success(
        request, f'🎉 কুইজ সম্পন্ন হয়েছে! আপনি {quiz.total_marks} এর মধ্যে {round(scaled_score, 1)} পেয়েছেন।')
    return redirect('dashboard')

    context = {'quiz': quiz, 'questions': questions}
    return render(request, 'students/take_manual_quiz.html', context)
