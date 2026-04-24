from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from .forms import CustomUserCreationForm, TestForm, QuestionForm, OptionForm
from .models import Test, Teacher, Student, Question, Option, User, TeacherStudent, Answer, TestResult
import json
from datetime import datetime

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
    return HttpResponse("Страница просмотра работ учеников")


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
                    order=index
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
                    order=index
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
    if request.method == 'POST':
        username = request.POST.get('username')
        try:
            student_user = User.objects.get(username=username, is_student=True)
            student = Student.objects.get(user=student_user)
            teacher_student, created = TeacherStudent.objects.get_or_create(
                teacher=teacher,
                student=student
            )
            if created:
                messages.success(request, f'Ученик {username} добавлен')
            else:
                messages.warning(request, f'Ученик {username} уже в вашем списке')
        except User.DoesNotExist:
            messages.error(request, f'Пользователь с логином {username} не найден')
        except Student.DoesNotExist:
            messages.error(request, f'Пользователь {username} не является учеником')
        return redirect('my_students')
    return render(request, 'teacher/add_student.html', {'user': request.user})

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
    # Список тестов учителя
    tests = Test.objects.filter(teacher=request.user)
    if request.method == 'POST':
        test_id = request.POST.get('test_id')
        deadline = request.POST.get('deadline')
        try:
            test = Test.objects.get(id=test_id, teacher=request.user)
            # Создаём запись о назначенном тесте (TestResult)
            test_result, created = TestResult.objects.get_or_create(
                student=student.user,  
                test=test,
                defaults={
                    'status': 'assigned',
                    'deadline': deadline if deadline else None,
                }
            )
            if not created:
                messages.warning(request, f'Тест "{test.title}" уже был назначен этому ученику')
            else:
                messages.success(request, f'Тест "{test.title}" назначен ученику {student.user.username}')
        except Test.DoesNotExist:
            messages.error(request, 'Тест не найден')
        return redirect('my_students')
    return render(request, 'teacher/assign_test.html', {
        'student': student,
        'tests': tests,
        'user': request.user,
    })

#список назначенных тестов у ученика
@login_required
def my_assigned_tests(request):
    assigned_tests = TestResult.objects.filter(
        student=request.user,
        status='assigned'
    ).select_related('test')
    return render(request, 'student/assigned_tests.html', {
        'assigned_tests': assigned_tests,
        'user': request.user,
    })

#страница прохождения теста учеником
@login_required
def take_test(request, test_id):
    # Проверяем, что тест назначен ученику
    try:
        test_result = TestResult.objects.get(
            student=request.user,
            test_id=test_id,
            status__in=['assigned', 'in_progress']
        )
    except TestResult.DoesNotExist:
        messages.error(request, 'Этот тест не назначен вам или уже пройден')
        return redirect('my_assigned_tests')
    test = test_result.test
    questions = test.questions.all().order_by('order', 'id')
    if test_result.status == 'assigned':
        test_result.status = 'in_progress'
        test_result.save()
    return render(request, 'student/take_test.html', {
        'test': test,
        'questions': questions,
        'test_result_id': test_result.id,
        'user': request.user,
    })

#прием ответов ученика и подсчет баллов
@login_required
def submit_test(request, test_id):
    try:
        test_result = TestResult.objects.get(
            student=request.user,
            test_id=test_id,
            status='in_progress'
        )
    except TestResult.DoesNotExist:
        messages.error(request, 'Этот тест не доступен для отправки')
        return redirect('my_assigned_tests')
    test = test_result.test
    questions = test.questions.all().order_by('order', 'id')
    total_score = 0
    max_score = 0
    for question in questions:
        max_score += 1
        if question.question_type == 'single':
            user_answer = request.POST.get(f'question_{question.id}')
            correct_option = question.options.filter(is_correct=True).first()
            is_correct = (user_answer and str(correct_option.id) == user_answer)
            if is_correct:
                total_score += 1
            Answer.objects.create(
                student=request.user,
                test=test,
                question=question,
                selected_option_id=user_answer if user_answer else None,
                is_correct=is_correct
            )
        elif question.question_type == 'multiple':
            user_answers = request.POST.getlist(f'question_{question.id}')
            correct_options = set(question.options.filter(is_correct=True).values_list('id', flat=True))
            user_answers_set = set(int(x) for x in user_answers)
            is_correct = (user_answers_set == correct_options)
            if is_correct:
                total_score += 1
            for answer_id in user_answers:
                Answer.objects.create(
                    student=request.user,
                    test=test,
                    question=question,
                    selected_option_id=answer_id,
                    is_correct=Answer.objects.filter(question=question, selected_option_id=answer_id, selected_option__is_correct=True).exists()
                )
        elif question.question_type == 'text':
            user_answer = request.POST.get(f'question_{question.id}', '')
            #развернутый ответ сохраняется без начисления баллов
            Answer.objects.create(
                student=request.user,
                test=test,
                question=question,
                answer_text=user_answer,
                is_correct=False  # пока не проверено
            )
    test_result.score = total_score
    test_result.status = 'completed'
    test_result.completed_at = datetime.now()
    test_result.save()
    messages.success(request, f'Тест завершён! Ваш результат: {total_score} из {max_score}')
    return redirect('my_assigned_tests')