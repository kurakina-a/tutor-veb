from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required

def home(request):
    return HttpResponse("""
        <h1>Добро пожаловать!</h1>
        <p>Это главная страница веб-сервиса для репетиторов</p>
        <a href="/register/">Регистрация</a><br>
        <a href="/login/">Вход</a>
    """)

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def teacher_dashboard(request):
    return HttpResponse("<h1>Личный кабинет репетитора</h1><p>Здесь будут тесты и ученики</p>")

@login_required
def student_dashboard(request):
    return HttpResponse("<h1>Личный кабинет ученика</h1><p>Здесь будут задания и результаты</p>")