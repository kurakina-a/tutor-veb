from django.contrib import admin
from .models import User, Teacher, Student, Test, Question, Option, Answer, Comment, TestResult, TeacherStudent

admin.site.register(User)
admin.site.register(Teacher)
admin.site.register(Student)

admin.site.register(Test)
admin.site.register(Question)
admin.site.register(Option)
admin.site.register(Answer)
admin.site.register(Comment)
admin.site.register(TestResult)
admin.site.register(TeacherStudent)