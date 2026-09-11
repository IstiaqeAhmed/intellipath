import os
import django
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import pickle

# ১. জ্যাঙ্গো এনভায়রনমেন্ট সেটআপ
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intellipath.settings')
django.setup()


def train_student_model():
    from django.contrib.auth.models import User
    from students.models import ExamResult, AssignmentSubmission, QuizResult

    print("ডাটাবেস থেকে ডেটা সংগ্রহ করা হচ্ছে...")

    users = User.objects.filter(is_superuser=False)
    data = []

    # ২. প্রতিটা স্টুডেন্টের ডেটা এক্সট্রাক্ট করা
    for user in users:
        # এক্সাম মার্কস (এটাই আমাদের মূল টার্গেট: পাস নাকি ফেল)
        exam_result = ExamResult.objects.filter(student=user).first()
        if not exam_result:
            continue
        exam_score = exam_result.score
        # পাস করলে 1, ফেল বা ড্রপআউট হলে 0
        passed_status = 1 if exam_result.passed else 0

        # অ্যাসাইনমেন্ট মার্কস
        assign_sub = AssignmentSubmission.objects.filter(student=user).first()
        assign_score = assign_sub.marks_obtained if assign_sub else 0

        # কুইজ মার্কস (ডাটাবেসে "8/10" টেক্সট হিসেবে আছে, তাই শুধু 8 কে আলাদা করতে হবে)
        quiz_result = QuizResult.objects.filter(user=user).first()
        if quiz_result and '/' in quiz_result.score:
            try:
                quiz_score = int(quiz_result.score.split('/')[0])
            except ValueError:
                quiz_score = 0
        else:
            quiz_score = 0

        # ডেটাবেস থেকে পাওয়া ডেটাগুলো লিস্টে যোগ করা
        data.append({
            'exam_score': exam_score,
            'assign_score': assign_score,
            'quiz_score': quiz_score,
            'passed_course': passed_status
        })

    # ৩. পান্ডাস (Pandas) ডেটাফ্রেম তৈরি
    df = pd.DataFrame(data)

    if df.empty:
        print("মডেল ট্রেইন করার জন্য কোনো ডেটা পাওয়া যায়নি!")
        return

    # ৪. ফিচারস (X) এবং টার্গেট (y) আলাদা করা
    X = df[['exam_score', 'assign_score', 'quiz_score']]
    y = df['passed_course']

    # ৫. ট্রেইনিং এবং টেস্টিং ডেটায় ভাগ করা (৮০% ট্রেইনিং, ২০% টেস্টিং)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42)

    print("মডেল ট্রেইনিং শুরু হচ্ছে...")

    # ৬. লজিস্টিক রিগ্রেশন মডেল কল এবং ফিট করা
    model = LogisticRegression()
    model.fit(X_train, y_train)

    # ৭. মডেলের পারফরম্যান্স/অ্যাকুরেসি চেক করা
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)

    print(f"✅ মডেল ট্রেইনিং সফলভাবে সম্পন্ন হয়েছে!")
    print(f"🎯 মডেলের অ্যাকুরেসি (Accuracy): {accuracy * 100:.2f}%")

    # ৮. মডেলটিকে পরবর্তীতে ব্যবহারের জন্য সেভ করা (Pickle File)
    with open('student_predictor_model.pkl', 'wb') as f:
        pickle.dump(model, f)

    print("মডেলটি 'student_predictor_model.pkl' নামে সেভ করা হয়েছে।")


if __name__ == "__main__":
    train_student_model()
