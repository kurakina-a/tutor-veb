from django import forms
#импорт моделей, с которыми работаем
from .models import User
from .models import Test, Question, Option
from django.utils import timezone

class CustomUserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label='Пароль')
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'password')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

class TestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ['title', 'description', 'deadline'] #какие поля показывать, остальные заполнятся автоматически
        widgets = { #как показывать поля
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    def clean_deadline(self): #проверка дедлайна
        deadline = self.cleaned_data.get('deadline')
        if deadline and deadline < timezone.now():
            raise forms.ValidationError("Дедлайн указан неверно!")
        return deadline

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'order']

class OptionForm(forms.ModelForm):
    class Meta:
        model = Option
        fields = ['text', 'is_correct']