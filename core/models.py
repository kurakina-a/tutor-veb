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
    description = models.TextField(blank=True, verbose_name='Описание')
    deadline = models.DateTimeField(null=True, blank=True, verbose_name='Дедлайн')  
    teacher = models.ForeignKey('User', on_delete=models.CASCADE, related_name='tests')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

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
    points = models.PositiveIntegerField(default=1, verbose_name='Баллы')
    
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
        ('pending_review', 'На проверке'),
        ('completed', 'Выполнен'),
    ]
    student = models.ForeignKey('User', on_delete=models.CASCADE, related_name='test_results')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='student_results')
    deadline = models.DateTimeField(null=True, blank=True, verbose_name='Дедлайн')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='assigned')
    score = models.PositiveIntegerField(null=True, blank=True, verbose_name='Баллы')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='Начало прохождения')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Завершён')
    
    class Meta: #настройки модели
        unique_together = ['student', 'test']  # один ученик - один результат на тест
    
    def __str__(self):
        return f"{self.student.username} - {self.test.title} ({self.status})"

class TeacherStudent(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='my_students')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='my_teacher')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['teacher', 'student']  # один ученик не может быть добавлен дважды

    def __str__(self):
        return f"{self.teacher.user.username} → {self.student.user.username}"

class Answer(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='answers')
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField(blank=True, null=True)  # для text
    selected_option = models.ForeignKey(Option, blank=True, null=True, on_delete=models.CASCADE)  # для single/multiple
    is_correct = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.student.username} - {self.question.text[:50]}"

class Comment(models.Model):
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='comments')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'is_teacher': True})
    text = models.TextField(verbose_name='Текст комментария')
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Комментарий к {self.answer.question.text[:30]} от {self.teacher.username}"