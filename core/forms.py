from django import forms
from django.utils import timezone
from .models import User, Test, Question, Option
import re


class CustomUserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label='Пароль')
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'password')

    def clean(self):
        cleaned_data = super().clean()

        username = cleaned_data.get('username')
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')
        password = cleaned_data.get('password')

        if not username or not first_name or not last_name or not password:
            raise forms.ValidationError("Заполните обязательные поля")

        return cleaned_data

    def clean_password(self):
        password = self.cleaned_data.get('password')

        if password:
            if len(password) <= 5:
                raise forms.ValidationError(
                    "Пароль слишком легкий (пароль должен содержать более 5 символов и хотя бы одну латинскую букву)"
                )

            if not re.search(r'[a-zA-Z]', password):
                raise forms.ValidationError(
                    "Пароль слишком легкий (пароль должен содержать более 5 символов и хотя бы одну латинскую букву)"
                )

        return password

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
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Название теста'}),
            'description': forms.Textarea(attrs={'placeholder': 'Описание теста', 'rows': 3}),
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'question_type', 'order']


class OptionForm(forms.ModelForm):
    class Meta:
        model = Option
        fields = ['text', 'is_correct']