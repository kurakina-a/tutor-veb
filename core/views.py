from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return HttpResponse("<h1>Добро пожаловать!</h1><p>Это главная страница веб-сервиса для репетиторов</p>")