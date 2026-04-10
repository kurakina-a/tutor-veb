from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, TestForm, QuestionForm, OptionForm
from django.contrib.auth.views import LoginView
from .models import Test, Question, Option


def home(request):
    return render(request, 'home.html')

def register(request):
    role = request.POST.get('role', 'student')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        
        if form.is_valid():
            user = form.save()
            
            # Устанавливаем роль
            if role == 'teacher':
                user.is_teacher = True
                user.is_student = False
            else:
                user.is_teacher = False
                user.is_student = True
            user.save()
            
            login(request, user)
            
            if user.is_teacher:
                return redirect('teacher_dashboard')
            else:
                return redirect('student_dashboard')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {
        'form': form,
        'role': role
    })

@login_required
def teacher_dashboard(request):
    context = {
        'user': request.user,
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'username': request.user.username,
    }
    return render(request, 'teacher/dashboard.html', context)
    
@login_required
def student_dashboard(request):
    context = {
        'user': request.user,
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'username': request.user.username,
    }
    return render(request, 'student/dashboard.html', context)

@login_required
def student_tasks(request):
    return render(request, 'student/tasks.html')

@login_required
def tests_list(request):
    return render(request, 'teacher/tests_list.html')

@login_required
def teacher_checking(request, student_id=None):
    return HttpResponse("Страница просмотра работ учеников")

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    def get_success_url(self):
        user = self.request.user
        if user.is_teacher:
            return '/teacher/dashboard/'
        elif user.is_student:
            return '/student/dashboard/'
        return '/'

#тесты текущего репетитора
@login_required
def test_list(request):
    tests = Test.objects.filter(teacher=request.user)
    return render(request, 'tests/list.html', {'tests': tests})

#создание нового теста
@login_required
def test_create(request):
    if request.method == 'POST': #если пользователь отправил форму
        form = TestForm(request.POST)
        if form.is_valid(): #если данные правильные
            test = form.save(commit=False)
            test.teacher = request.user
            test.save() #сохранить в БД
            return redirect('test_edit', test_id=test.id) #переход на другую страницу
    else: #если просто открыта страница
        form = TestForm()
    return render(request, 'tests/create.html', {'form': form}) #показывается форма

#редактирование теста
@login_required
def test_edit(request, test_id):
    test = get_object_or_404(Test, id=test_id, teacher=request.user)
    
    if request.method == 'POST':
        form = TestForm(request.POST, instance=test)
        if form.is_valid():
            form.save()
            return redirect('test_list')
    else:
        form = TestForm(instance=test)
    
    return render(request, 'tests/edit.html', {'form': form, 'test': test})

#удаление теста
@login_required
def test_delete(request, test_id):
    test = get_object_or_404(Test, id=test_id, teacher=request.user)
    if request.method == 'POST':
        test.delete()
        return redirect('test_list')
    return render(request, 'tests/delete.html', {'test': test})