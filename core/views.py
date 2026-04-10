from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm
from django.contrib.auth.views import LoginView

def home(request):
    return render(request, 'home.html')

def register(request):
    role = request.GET.get('role', 'student')
    
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
        elif hasattr(user, 'student'):
            return '/student/dashboard/'
        return '/'

