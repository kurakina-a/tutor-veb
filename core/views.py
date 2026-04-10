from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from .forms import CustomUserCreationForm, TestForm
from .models import Test, Teacher, Student, Question


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
    return render(request, 'tests/list.html', {'tests': tests})


@login_required
def test_create(request):
    if request.method == 'POST':
        form = TestForm(request.POST)
        if form.is_valid():
            test = form.save(commit=False)
            test.teacher = request.user
            test.save()
            return redirect('test_edit', test_id=test.id)
    else:
        form = TestForm()

    return render(request, 'tests/create.html', {
        'form': form,
        'user': request.user,
    })


@login_required
def test_edit(request, test_id):
    test = get_object_or_404(Test, id=test_id, teacher=request.user)
    questions = Question.objects.filter(test=test).order_by('order', 'id')

    if request.method == 'POST':
        form = TestForm(request.POST, instance=test)
        if form.is_valid():
            form.save()
            return redirect('test_list')
    else:
        form = TestForm(instance=test)

    return render(request, 'tests/edit.html', {
        'form': form,
        'test': test,
        'questions': questions,
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