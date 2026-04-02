from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm
from django.contrib.auth.views import LoginView

def home(request):
    return HttpResponse("""
        <h1>Добро пожаловать!</h1>
        <p>Это главная страница веб-сервиса для репетиторов</p>
        <a href="/register/">Регистрация</a><br>
        <a href="/login/">Вход</a>
    """)

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            if user.is_teacher:
                return redirect('teacher_dashboard')
            else:
                return redirect('student_dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def teacher_dashboard(request):
    return HttpResponse("<h1>Личный кабинет репетитора</h1><p>Здесь будут тесты и ученики</p>")

@login_required
def student_dashboard(request):
    return HttpResponse("<h1>Личный кабинет ученика</h1><p>Здесь будут задания и результаты</p>")

class CustomLoginView(LoginView):
    def get_success_url(self):
        user = self.request.user
        if user.is_teacher:
            return '/teacher/'
        elif user.is_student:
            return '/student/'
        return '/'