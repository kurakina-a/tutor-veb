from django import forms
from .models import User, Test, Question, Option
import re


class CustomUserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label='Пароль')
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'password')

    def clean_password(self):
        password = self.cleaned_data.get('password')

        # длина
        if len(password) < 5:
            raise forms.ValidationError(
                "Пароль слишком легкий (пароль должен содержать более 4 символов и хотя бы одну латинскую букву)"
            )

        # латинские буквы
        if not re.search(r'[a-zA-Z]', password):
            raise forms.ValidationError(
                "Пароль слишком легкий (пароль должен содержать более 4 символов и хотя бы одну латинскую букву)"
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
        



class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'question_type', 'order']

class OptionForm(forms.ModelForm):
    class Meta:
        model = Option
        fields = ['text', 'is_correct']