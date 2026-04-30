from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from .forms import CustomUserCreationForm, TestForm, QuestionForm, OptionForm
from .models import Test, Teacher, Student, Question, Option, User, TeacherStudent, Answer, TestResult, Comment
import json
from datetime import datetime
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now
from django.utils import timezone


def home(request):
    return render(request, 'home.html')


def register(request):
    role = request.GET.get('role') or request.POST.get('role') or 'student'

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)

            user.username = form.cleaned_data['username']
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.set_password(form.cleaned_data['password'])

            if role == 'teacher':
                user.is_teacher = True
                user.is_student = False
            else:
                user.is_teacher = False
                user.is_student = True

            user.save()

            if role == 'teacher':
                Teacher.objects.get_or_create(user=user)
            else:
                Student.objects.get_or_create(user=user)

            login(request, user)

            if user.is_teacher:
                return redirect('teacher_dashboard')
            return redirect('student_dashboard')
        else:
            print("Ошибки формы:", form.errors)
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/register.html', {
        'form': form,
        'role': role
    })


@login_required
def teacher_dashboard(request):
    return render(request, 'teacher/dashboard.html', {
        'user': request.user,
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'username': request.user.username,
        'role': 'Преподаватель',
    })


@login_required
def student_dashboard(request):
    return render(request, 'student/dashboard.html', {
        'user': request.user,
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'username': request.user.username,
        'role': 'Ученик',
    })


@login_required
def student_tasks(request):
    return render(request, 'student/tasks.html')


@login_required
def tests_list(request):
    tests = Test.objects.filter(teacher=request.user)
    return render(request, 'teacher/tests_list.html', {
        'tests': tests,
        'user': request.user,
    })


@login_required
def teacher_checking(request, student_id=None):
    teacher = Teacher.objects.get(user=request.user)

    teacher_student = get_object_or_404(
        TeacherStudent,
        teacher=teacher,
        student_id=student_id
    )

    student = teacher_student.student

    results = TestResult.objects.filter(
        student=student.user,
        test__teacher=request.user
    ).select_related('test').order_by('-id')

    rows = []

    for result in results:
        if result.deadline and result.deadline < timezone.now() and result.status == 'assigned':
            display_status = 'Дедлайн просрочен'
        elif result.status == 'assigned':
            display_status = 'Назначен'
        elif result.status == 'pending_review':
            display_status = 'На проверке'
        elif result.status == 'completed':
            display_status = 'Выполнен'
        else:
            display_status = result.status

        max_score = sum(question.points for question in result.test.questions.all())

        rows.append({
            'result': result,
            'display_status': display_status,
            'max_score': max_score,
        })

    return render(request, 'teacher/student_results.html', {
        'student': student,
        'rows': rows,
        'user': request.user,
    })


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role'] = self.request.GET.get('role') or self.request.POST.get('role') or 'student'
        return context

    def form_valid(self, form):
        role = self.request.POST.get('role') or self.request.GET.get('role') or 'student'
        user = form.get_user()

        if role == 'teacher' and not user.is_teacher:
            form.add_error(None, "Несоответствие роли")
            return self.form_invalid(form)

        if role == 'student' and not user.is_student:
            form.add_error(None, "Несоответствие роли")
            return self.form_invalid(form)

        login(self.request, user)
        return redirect(self.get_success_url())

    def get_success_url(self):
        user = self.request.user

        if user.is_teacher:
            return '/teacher/dashboard/'
        return '/student/dashboard/'


@login_required
def test_list(request):
    tests = Test.objects.filter(teacher=request.user)
    return render(request, 'tests/list.html', {
        'tests': tests,
        'user': request.user,
    })


def _build_questions_data(test):
    result = []

    for question in test.questions.all().order_by('order', 'id'):
        item = {
            'text': question.text,
            'question_type': question.question_type,
            'points': question.points,
            'options': []
        }

        if question.question_type != 'text':
            for option in question.options.all():
                item['options'].append({
                    'text': option.text,
                    'is_correct': option.is_correct
                })

        result.append(item)

    return result


def _parse_questions_from_post(request):
    raw = request.POST.get('questions_data', '')
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def _validate_questions_data(questions_data):
    errors = []

    if not questions_data:
        errors.append('Добавьте хотя бы 1 вопрос')
        return errors

    for index, question in enumerate(questions_data, start=1):
        text = (question.get('text') or '').strip()
        question_type = question.get('question_type') or 'single'
        options = question.get('options') or []

        if not text:
            errors.append(f'Вопрос {index}: заполните текст вопроса')
            continue

        if question_type in ['single', 'multiple']:
            non_empty_options = []
            for option in options:
                option_text = (option.get('text') or '').strip()
                if option_text:
                    non_empty_options.append(option)

            if len(non_empty_options) < 2:
                errors.append(f'Вопрос {index}: добавьте минимум 2 варианта ответа')
                continue

            correct_count = sum(1 for option in non_empty_options if option.get('is_correct'))

            if question_type == 'single' and correct_count != 1:
                errors.append(f'Вопрос {index}: для "Один вариант" должен быть ровно 1 правильный ответ')

            if question_type == 'multiple' and correct_count < 1:
                errors.append(f'Вопрос {index}: для "Множественный выбор" нужен хотя бы 1 правильный ответ')

    return errors


@login_required
def test_create(request):
    if request.method == 'POST':
        form = TestForm(request.POST)
        posted_questions_data = _parse_questions_from_post(request)
        question_errors = _validate_questions_data(posted_questions_data)

        if form.is_valid() and not question_errors:
            test = form.save(commit=False)
            test.teacher = request.user
            test.save()

            for index, q in enumerate(posted_questions_data, start=1):
                text = (q.get('text') or '').strip()
                question_type = q.get('question_type') or 'single'
                options = q.get('options') or []

                if not text:
                    continue

                question = Question.objects.create(
                    test=test,
                    text=text,
                    question_type=question_type,
                    order=index,
                    points=int(q.get('points') or 1)
                )

                if question_type != 'text':
                    for opt in options:
                        option_text = (opt.get('text') or '').strip()
                        if not option_text:
                            continue

                        Option.objects.create(
                            question=question,
                            text=option_text,
                            is_correct=bool(opt.get('is_correct'))
                        )

            return redirect('test_list')

        return render(request, 'tests/create.html', {
            'form': form,
            'questions_data': posted_questions_data,
            'question_errors': question_errors,
            'user': request.user,
        })

    form = TestForm()

    return render(request, 'tests/create.html', {
        'form': form,
        'questions_data': [],
        'question_errors': [],
        'user': request.user,
    })


@login_required
def test_edit(request, test_id):
    test = get_object_or_404(Test, id=test_id, teacher=request.user)

    if request.method == 'POST':
        form = TestForm(request.POST, instance=test)
        posted_questions_data = _parse_questions_from_post(request)
        question_errors = _validate_questions_data(posted_questions_data)

        if form.is_valid() and not question_errors:
            test = form.save()

            test.questions.all().delete()

            for index, q in enumerate(posted_questions_data, start=1):
                text = (q.get('text') or '').strip()
                question_type = q.get('question_type') or 'single'
                options = q.get('options') or []

                if not text:
                    continue

                question = Question.objects.create(
                    test=test,
                    text=text,
                    question_type=question_type,
                    order=index,
                    points=int(q.get('points') or 1)
                )

                if question.question_type != 'text':
                    for opt in options:
                        option_text = (opt.get('text') or '').strip()
                        if not option_text:
                            continue

                        Option.objects.create(
                            question=question,
                            text=option_text,
                            is_correct=bool(opt.get('is_correct'))
                        )

            return redirect('test_list')

        return render(request, 'tests/edit.html', {
            'form': form,
            'test': test,
            'questions_data': posted_questions_data,
            'question_errors': question_errors,
            'user': request.user,
        })

    form = TestForm(instance=test)

    return render(request, 'tests/edit.html', {
        'form': form,
        'test': test,
        'questions_data': _build_questions_data(test),
        'question_errors': [],
        'user': request.user,
    })


@login_required
def test_delete(request, test_id):
    test = get_object_or_404(Test, id=test_id, teacher=request.user)

    if request.method == 'POST':
        test.delete()
        return redirect('test_list')

    return render(request, 'tests/delete.html', {
        'test': test,
        'user': request.user,
    })


@login_required
def question_add(request, test_id):
    test = get_object_or_404(Test, id=test_id, teacher=request.user)
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.test = test
            question.save()
            return redirect('test_edit', test_id=test.id)
    else:
        form = QuestionForm()
    return render(request, 'tests/question_form.html', {
        'form': form,
        'test': test,
        'title': 'Добавить вопрос',
        'user': request.user,
    })


@login_required
def question_edit(request, question_id):
    question = get_object_or_404(Question, id=question_id, test__teacher=request.user)
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            return redirect('test_edit', test_id=question.test.id)
    else:
        form = QuestionForm(instance=question)
    return render(request, 'tests/question_form.html', {
        'form': form,
        'question': question,
        'test': question.test,
        'title': 'Редактировать вопрос',
        'user': request.user,
    })


@login_required
def question_delete(request, question_id):
    question = get_object_or_404(Question, id=question_id, test__teacher=request.user)
    test_id = question.test.id
    if request.method == 'POST':
        question.delete()
        return redirect('test_edit', test_id=test_id)
    return render(request, 'tests/question_confirm_delete.html', {
        'question': question,
        'user': request.user,
    })


@login_required
def option_add(request, question_id):
    question = get_object_or_404(Question, id=question_id, test__teacher=request.user)
    if request.method == 'POST':
        form = OptionForm(request.POST)
        if form.is_valid():
            option = form.save(commit=False)
            option.question = question
            option.save()
            return redirect('test_edit', test_id=question.test.id)
    else:
        form = OptionForm()
    return render(request, 'tests/option_form.html', {
        'form': form,
        'question': question,
        'title': 'Добавить вариант ответа',
        'user': request.user,
    })


@login_required
def option_edit(request, option_id):
    option = get_object_or_404(Option, id=option_id, question__test__teacher=request.user)
    if request.method == 'POST':
        form = OptionForm(request.POST, instance=option)
        if form.is_valid():
            form.save()
            return redirect('test_edit', test_id=option.question.test.id)
    else:
        form = OptionForm(instance=option)
    return render(request, 'tests/option_form.html', {
        'form': form,
        'option': option,
        'title': 'Редактировать вариант',
        'user': request.user,
    })


@login_required
def option_delete(request, option_id):
    option = get_object_or_404(Option, id=option_id, question__test__teacher=request.user)
    test_id = option.question.test.id
    if request.method == 'POST':
        option.delete()
        return redirect('test_edit', test_id=test_id)
    return render(request, 'tests/option_confirm_delete.html', {
        'option': option,
        'user': request.user,
    })

@login_required
def my_students(request):
    teacher = Teacher.objects.get(user=request.user)
    students = teacher.my_students.all()  
    return render(request, 'teacher/students.html', {
        'students': students,
        'user': request.user,
    })



@login_required
def add_student(request):
    teacher = Teacher.objects.get(user=request.user)

    error = None
    success = None
    username_value = ''

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        username_value = username

        if not username:
            error = 'Введите логин ученика'
        else:
            try:
                student_user = User.objects.get(username=username, is_student=True)
                student = Student.objects.get(user=student_user)

                teacher_student, created = TeacherStudent.objects.get_or_create(
                    teacher=teacher,
                    student=student
                )

                if created:
                    success = f'Ученик {username} добавлен'
                    username_value = ''
                else:
                    error = f'Ученик {username} уже есть в вашем списке'

            except User.DoesNotExist:
                error = 'Такого пользователя не существует'
            except Student.DoesNotExist:
                error = 'Этот пользователь не является учеником'

    return render(request, 'teacher/add_student.html', {
        'user': request.user,
        'error': error,
        'success': success,
        'username_value': username_value,
    })
    
#назначить тест ученику
@login_required
def assign_test(request, student_id):
    teacher = Teacher.objects.get(user=request.user)

    try:
        teacher_student = TeacherStudent.objects.get(teacher=teacher, student_id=student_id)
        student = teacher_student.student
    except TeacherStudent.DoesNotExist:
        messages.error(request, 'Этот ученик не привязан к вам')
        return redirect('my_students')

    tests = Test.objects.filter(teacher=request.user)

    error = None
    success = None

    if request.method == 'POST':
        test_id = request.POST.get('test_id')
        deadline_raw = request.POST.get('deadline')

        if not test_id:
            error = 'Выберите тест'
        else:
            try:
                test = Test.objects.get(id=test_id, teacher=request.user)
                deadline = parse_datetime(deadline_raw) if deadline_raw else None

                test_result, created = TestResult.objects.get_or_create(
                    student=student.user,
                    test=test,
                    defaults={
                        'status': 'assigned',
                        'deadline': deadline,
                    }
                )

                if not created:
                    error = f'Тест "{test.title}" уже был назначен этому ученику'
                else:
                    success = f'Тест "{test.title}" назначен ученику {student.user.username}'

            except Test.DoesNotExist:
                error = 'Тест не найден'

    return render(request, 'teacher/assign_test.html', {
        'student': student,
        'tests': tests,
        'user': request.user,
        'error': error,
        'success': success,
        'selected_test_id': request.POST.get('test_id', ''),
        'deadline_value': request.POST.get('deadline', ''),
    })
#список назначенных тестов у ученика
@login_required
def my_assigned_tests(request):
    assigned_tests = TestResult.objects.filter(
        student=request.user
    ).select_related('test').order_by('-id')

    return render(request, 'student/assigned_test.html', {
        'assigned_tests': assigned_tests,
        'user': request.user,
    })

def _build_take_question_items(test, post_data=None, question_errors=None):
    items = []

    for question in test.questions.all().order_by('order', 'id'):
        error = question_errors.get(question.id) if question_errors else None

        item = {
            'question': question,
            'error': error,
            'options': [],
            'answer_text': '',
        }

        if post_data:
            if question.question_type == 'text':
                item['answer_text'] = post_data.get(f'question_{question.id}', '')

            selected_values = post_data.getlist(f'question_{question.id}')

            for option in question.options.all():
                item['options'].append({
                    'option': option,
                    'checked': str(option.id) in selected_values,
                })
        else:
            for option in question.options.all():
                item['options'].append({
                    'option': option,
                    'checked': False,
                })

        items.append(item)

    return items

#страница прохождения теста учеником
@login_required
def take_test(request, test_id):
    try:
        test_result = TestResult.objects.get(
            student=request.user,
            test_id=test_id,
            status='assigned'
        )
    except TestResult.DoesNotExist:
        messages.error(request, 'Этот тест не назначен вам или уже пройден')
        return redirect('my_assigned_tests')

    if test_result.deadline and test_result.deadline < timezone.now():
        messages.error(request, f'Дедлайн теста истёк {test_result.deadline.strftime("%d.%m.%Y %H:%M")}')
        return redirect('my_assigned_tests')

    test = test_result.test
    question_items = _build_take_question_items(test)

    return render(request, 'student/take_test.html', {
        'test': test,
        'question_items': question_items,
        'test_result_id': test_result.id,
        'user': request.user,
        'general_error': None,
    })
#прием ответов ученика и подсчет баллов
@login_required
def submit_test(request, test_id):
    try:
        test_result = TestResult.objects.get(
            student=request.user,
            test_id=test_id,
            status='assigned'
        )
    except TestResult.DoesNotExist:
        messages.error(request, 'Этот тест не доступен для отправки')
        return redirect('my_assigned_tests')

    if test_result.deadline and test_result.deadline < timezone.now():
        messages.error(request, 'Дедлайн теста истёк')
        return redirect('my_assigned_tests')

    test = test_result.test
    questions = test.questions.all().order_by('order', 'id')

    question_errors = {}

    for question in questions:
        field_name = f'question_{question.id}'

        if question.question_type == 'single':
            if not request.POST.get(field_name):
                question_errors[question.id] = 'Выберите один вариант ответа'

        elif question.question_type == 'multiple':
            if not request.POST.getlist(field_name):
                question_errors[question.id] = 'Выберите хотя бы один вариант ответа'

        elif question.question_type == 'text':
            if not request.POST.get(field_name, '').strip():
                question_errors[question.id] = 'Введите развёрнутый ответ'

    if question_errors:
        question_items = _build_take_question_items(
            test,
            post_data=request.POST,
            question_errors=question_errors
        )

        return render(request, 'student/take_test.html', {
            'test': test,
            'question_items': question_items,
            'test_result_id': test_result.id,
            'user': request.user,
            'general_error': 'Ответьте на все вопросы',
        })

    total_score = 0
    max_score = 0

    Answer.objects.filter(
        student=request.user,
        test=test
    ).delete()

    for question in questions:
        max_score += question.points

        if question.question_type == 'single':
            user_answer = request.POST.get(f'question_{question.id}')
            correct_option = question.options.filter(is_correct=True).first()

            is_correct = False
            if user_answer and correct_option:
                is_correct = int(user_answer) == correct_option.id

            if is_correct:
                total_score += question.points

            Answer.objects.create(
                student=request.user,
                test=test,
                question=question,
                selected_option_id=user_answer,
                is_correct=is_correct
            )

        elif question.question_type == 'multiple':
            user_answers = request.POST.getlist(f'question_{question.id}')

            correct_options = set(
                question.options.filter(is_correct=True).values_list('id', flat=True)
            )

            user_answers_set = set(int(item) for item in user_answers if item)

            is_correct = user_answers_set == correct_options

            if is_correct:
                total_score += question.points

            for option_id in user_answers_set:
                Answer.objects.create(
                    student=request.user,
                    test=test,
                    question=question,
                    selected_option_id=option_id,
                    is_correct=option_id in correct_options
                )

        elif question.question_type == 'text':
            user_answer = request.POST.get(f'question_{question.id}', '').strip()

            Answer.objects.create(
                student=request.user,
                test=test,
                question=question,
                answer_text=user_answer,
                is_correct=False
            )

    has_text_questions = questions.filter(question_type='text').exists()

    test_result.score = total_score

    if has_text_questions:
        test_result.status = 'pending_review'
    else:
        test_result.status = 'completed'

    test_result.completed_at = timezone.now()
    test_result.save()

    return redirect('test_results', test_result_id=test_result.id)


#страница с результатами теста
@login_required
def test_results(request, test_result_id):
    try:
        test_result = TestResult.objects.get(
            id=test_result_id,
            student=request.user
        )
    except TestResult.DoesNotExist:
        messages.error(request, 'Результат не найден')
        return redirect('my_assigned_tests')

    test = test_result.test

    answers = Answer.objects.filter(
        student=request.user,
        test=test
    ).select_related('question', 'selected_option')

    questions_details = []

    for question in test.questions.all().order_by('order', 'id'):
        question_answers = answers.filter(question=question)

        selected_option_ids = set(
            answer.selected_option_id
            for answer in question_answers
            if answer.selected_option_id
        )

        answer_for_comment = question_answers.first()

        comments = []
        if answer_for_comment:
            comments = Comment.objects.filter(
                answer=answer_for_comment
            ).select_related('teacher').order_by('created_at')

        options = []

        if question.question_type != 'text':
            for option in question.options.all():
                options.append({
                    'id': option.id,
                    'text': option.text,
                    'is_correct': option.is_correct,
                    'is_selected': option.id in selected_option_ids,
                })

        if question.question_type == 'multiple':
            correct_option_ids = set(
                question.options.filter(is_correct=True).values_list('id', flat=True)
            )

            is_correct = selected_option_ids == correct_option_ids

            if selected_option_ids:
                user_answer = ', '.join(
                    option.text
                    for option in question.options.filter(id__in=selected_option_ids)
                )
            else:
                user_answer = '(не выбран)'

            status = 'Правильно' if is_correct else 'Неправильно'
            earned_points = question.points if is_correct else 0

        else:
            answer = question_answers.first()

            if question.question_type == 'text':
                user_answer = answer.answer_text if answer and answer.answer_text else '(не введён)'
                is_correct = answer.is_correct if answer else False
                status = 'Проверен' if is_correct else 'Ожидает проверки'
                earned_points = None
            else:
                user_answer = answer.selected_option.text if answer and answer.selected_option else '(не выбран)'
                is_correct = answer.is_correct if answer else False
                status = 'Правильно' if is_correct else 'Неправильно'
                earned_points = question.points if is_correct else 0

        questions_details.append({
            'text': question.text,
            'type': question.question_type,
            'user_answer': user_answer,
            'selected_option': user_answer,
            'options': options,
            'is_correct': is_correct,
            'status': status,
            'points': question.points,
            'earned_points': earned_points,
            'comments': comments,
        })

    max_score = sum(question.points for question in test.questions.all())

    return render(request, 'student/results.html', {
        'test': test,
        'test_result': test_result,
        'questions_details': questions_details,
        'max_score': max_score,
        'user': request.user,
    })
    


@login_required
def teacher_result_detail(request, test_result_id):
    test_result = get_object_or_404(
        TestResult,
        id=test_result_id,
        test__teacher=request.user
    )

    test = test_result.test

    if request.method == 'POST':
        answer_id = request.POST.get('answer_id')
        comment_text = request.POST.get('comment_text', '').strip()

        if answer_id and comment_text:
            answer = get_object_or_404(
                Answer,
                id=answer_id,
                question__test__teacher=request.user
            )

            Comment.objects.create(
                answer=answer,
                teacher=request.user,
                text=comment_text
            )

            messages.success(request, 'Комментарий сохранён')
        else:
            messages.error(request, 'Комментарий не может быть пустым')

        return redirect('teacher_result_detail', test_result_id=test_result.id)

    answers = Answer.objects.filter(
        student=test_result.student,
        test=test
    ).select_related('question', 'selected_option')

    questions_details = []

    for question in test.questions.all().order_by('order', 'id'):
        question_answers = answers.filter(question=question)

        selected_option_ids = set(
            answer.selected_option_id
            for answer in question_answers
            if answer.selected_option_id
        )

        answer_for_comment = question_answers.first()

        comments = []
        if answer_for_comment:
            comments = Comment.objects.filter(
                answer=answer_for_comment
            ).select_related('teacher').order_by('created_at')

        options = []

        if question.question_type != 'text':
            for option in question.options.all():
                options.append({
                    'id': option.id,
                    'text': option.text,
                    'is_correct': option.is_correct,
                    'is_selected': option.id in selected_option_ids,
                })

        if question.question_type == 'multiple':
            correct_option_ids = set(
                question.options.filter(is_correct=True).values_list('id', flat=True)
            )

            is_correct = selected_option_ids == correct_option_ids

            if selected_option_ids:
                user_answer = ', '.join(
                    option.text
                    for option in question.options.filter(id__in=selected_option_ids)
                )
            else:
                user_answer = '(не выбран)'

        else:
            answer = question_answers.first()

            if question.question_type == 'text':
                user_answer = answer.answer_text if answer and answer.answer_text else '(не введён)'
                is_correct = answer.is_correct if answer else False
            else:
                user_answer = answer.selected_option.text if answer and answer.selected_option else '(не выбран)'
                is_correct = answer.is_correct if answer else False

        questions_details.append({
            'text': question.text,
            'type': question.question_type,
            'user_answer': user_answer,
            'selected_option': user_answer,
            'options': options,
            'is_correct': is_correct,
            'points': question.points,
            'answer_id': answer_for_comment.id if answer_for_comment else None,
            'comments': comments,
        })

    max_score = sum(question.points for question in test.questions.all())

    return render(request, 'teacher/result_detail.html', {
        'test': test,
        'test_result': test_result,
        'questions_details': questions_details,
        'answers_count': answers.count(),
        'max_score': max_score,
        'user': request.user,
    })


#список ответов на развернутые вопросы, ожидающих комментария
@login_required
def pending_answers(request):
    pending = Answer.objects.filter(
        question__question_type='text',
        is_correct=False,
        question__test__teacher=request.user
    ).select_related('student', 'question__test').order_by('-id')
    return render(request, 'teacher/pending_answers.html', {
        'pending': pending,
        'user': request.user,
    })

#добавление комментария к ответу ученика
@login_required
def add_comment(request, answer_id):
    answer = get_object_or_404(Answer, id=answer_id, question__test__teacher=request.user)
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if text:
            Comment.objects.create(
                answer=answer,
                teacher=request.user,
                text=text
            )
            answer.is_correct = True
            answer.save()
            messages.success(request, 'Комментарий добавлен')
        else:
            messages.error(request, 'Текст комментария не может быть пустым')
        return redirect('pending_answers')
    return render(request, 'teacher/add_comment.html', {
        'answer': answer,
        'user': request.user,
    })


#комментарии репетиторов к ответам ученика
@login_required
def my_comments(request):
    comments = Comment.objects.filter(
        answer__student=request.user
    ).select_related('answer__question', 'answer__test', 'teacher').order_by('-created_at')
    return render(request, 'student/my_comments.html', {
        'comments': comments,
        'user': request.user,
    })
    
@login_required
def review_text_answers(request, test_result_id):
    test_result = get_object_or_404(
        TestResult,
        id=test_result_id,
        test__teacher=request.user
    )

    answers = Answer.objects.filter(
        student=test_result.student,
        test=test_result.test,
        question__question_type='text',
        is_correct=False
    ).select_related('student', 'test', 'question').order_by('question__order', 'id')

    return render(request, 'teacher/review_text.html', {
        'test_result': test_result,
        'answers': answers,
        'user': request.user,
    })


#выставление оценки за развернутый ответ
@login_required
def grade_answer(request, answer_id):
    answer = get_object_or_404(
        Answer,
        id=answer_id,
        question__test__teacher=request.user
    )

    test_result = get_object_or_404(
        TestResult,
        student=answer.student,
        test=answer.test
    )

    max_points = answer.question.points

    if request.method == 'POST':
        score_raw = request.POST.get('score', '').strip()
        comment_text = request.POST.get('text', '').strip()

        error = None
        score_value = None

        if not score_raw:
            error = 'Введите количество баллов'
        else:
            try:
                score_value = int(score_raw)

                if score_value < 0:
                    error = 'Баллы не могут быть меньше 0'
                elif score_value > max_points:
                    error = f'Максимум за этот вопрос — {max_points} балл.'

            except ValueError:
                error = 'Введите корректное число'

        if error:
            return render(request, 'teacher/grade_answer.html', {
                'answer': answer,
                'test_result': test_result,
                'max_points': max_points,
                'error': error,
                'score_value': score_raw,
                'comment_value': comment_text,
                'user': request.user,
            })

        answer.is_correct = True
        answer.save()

        current_score = test_result.score or 0
        test_result.score = current_score + score_value

        unfinished_text_answers = Answer.objects.filter(
            student=answer.student,
            test=answer.test,
            question__question_type='text',
            is_correct=False
        ).exclude(id=answer.id)

        if not unfinished_text_answers.exists():
            test_result.status = 'completed'

        test_result.save()

        if comment_text:
            Comment.objects.create(
                answer=answer,
                teacher=request.user,
                text=comment_text
            )

        messages.success(request, 'Ответ проверен')

        return redirect('review_text_answers', test_result_id=test_result.id)

    return render(request, 'teacher/grade_answer.html', {
        'answer': answer,
        'test_result': test_result,
        'max_points': max_points,
        'error': None,
        'score_value': '',
        'comment_value': '',
        'user': request.user,
    })