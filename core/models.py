from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    is_teacher = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    def __str__(self):
        return self.user.username

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    def __str__(self):
        return self.user.username

class Test(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название теста')
    description = models.TextField(blank=True, verbose_name='Описание') #описание теста (true - может быть пустым)
    deadline = models.DateTimeField(null=True, blank=True, verbose_name='Дедлайн')
    teacher = models.ForeignKey('User', on_delete=models.CASCADE, related_name='tests') #связь с User, CASCADE - если удалить учителя, удалится тест
    created_at = models.DateTimeField(auto_now_add=True) #дата и время создания записываются автоматически
    def __str__(self): 
        return self.title  #при выводе вместо Test object будет написано название теста

class Question(models.Model):
    QUESTION_TYPES = [
        ('single', 'Один вариант'),
        ('multiple', 'Множественный выбор'),
        ('text', 'Развёрнутый ответ'),
    ]
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField(verbose_name='Текст вопроса')
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES, default='single', verbose_name='Тип вопроса')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    
    def __str__(self):
        return f"{self.text[:50]}... ({self.get_question_type_display()})"
    
    class Meta:
        ordering = ['order', 'id']

class Option(models.Model): #варианты ответа на вопрос
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=300, verbose_name='Текст варианта')
    is_correct = models.BooleanField(default=False, verbose_name='Правильный?')
    def __str__(self):
        return self.text

class TestResult(models.Model): #результат прохождения теста
    STATUS_CHOICES = [
        ('assigned', 'Назначен'),
        ('in_progress', 'В процессе'),
        ('completed', 'Завершён'),
    ]
    student = models.ForeignKey('User', on_delete=models.CASCADE, related_name='test_results')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='student_results')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='assigned')
    score = models.PositiveIntegerField(null=True, blank=True, verbose_name='Баллы')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='Начало прохождения')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Завершён')
    
    class Meta: #настройки модели
        unique_together = ['student', 'test']  # один ученик - один результат на тест
    
    def __str__(self):
        return f"{self.student.username} - {self.test.title} ({self.status})"