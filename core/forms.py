from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Teacher, Student

class CustomUserCreationForm(UserCreationForm):
    USER_TYPE_CHOICES = (
        ('teacher', 'Я репетитор'),
        ('student', 'Я ученик'),
    )
    user_type = forms.ChoiceField(choices=USER_TYPE_CHOICES, widget=forms.RadioSelect, label='Кто вы?')

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'user_type')

    def save(self, commit=True):
        user = super().save(commit=False)
        user_type = self.cleaned_data.get('user_type')
        if commit:
            user.save()
            if user_type == 'teacher':
                user.is_teacher = True
                Teacher.objects.create(user=user)
            else:
                user.is_student = True
                Student.objects.create(user=user)
            user.save()
        return user