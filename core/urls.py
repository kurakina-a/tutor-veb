from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    #главная и авторизация
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.CustomLoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
    #личные кабинеты
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    
    path('student/tasks/', views.student_tasks, name='student_tasks'),
    path('teacher/tests/', views.tests_list, name='tests_list'),
    path('teacher/students/<int:student_id>/results/', views.teacher_checking, name='teacher_checking'),
    #тесты
    path('tests/', views.test_list, name='test_list'),
    path('tests/create/', views.test_create, name='test_create'),
    path('tests/<int:test_id>/edit/', views.test_edit, name='test_edit'),
    path('tests/<int:test_id>/delete/', views.test_delete, name='test_delete'),

    #вопросы
    path('tests/question/add/<int:test_id>/', views.question_add, name='question_add'),
    path('question/edit/<int:question_id>/', views.question_edit, name='question_edit'),
    path('question/delete/<int:question_id>/', views.question_delete, name='question_delete'),

    #варианты ответов
    path('question/option/add/<int:question_id>/', views.option_add, name='option_add'),
    path('option/edit/<int:option_id>/', views.option_edit, name='option_edit'),
    path('option/delete/<int:option_id>/', views.option_delete, name='option_delete'),

    #назначение теста ученику
    path('teacher/students/', views.my_students, name='my_students'),
    path('teacher/students/add/', views.add_student, name='add_student'),
    path('teacher/assign_test/<int:student_id>/', views.assign_test, name='assign_test'),
    path('student/tests/', views.my_assigned_tests, name='my_assigned_tests'),
    path('tests/take/<int:test_id>/', views.take_test, name='take_test'),
    path('tests/submit/<int:test_id>/', views.submit_test, name='submit_test'),
    path('results/<int:test_result_id>/', views.test_results, name='test_results'),
    path('teacher/result/<int:test_result_id>/', views.teacher_result_detail, name='teacher_result_detail')
]