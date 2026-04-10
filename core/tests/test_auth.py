from django.test import TestCase
from django.urls import reverse #имя маршрутов в URL
from django.contrib.auth import get_user_model

User = get_user_model()

# self.client - имитация браузера 
# .post - отправляем форму 
# ' ' - куда отправляем 
# { } - данные формы response — ответ сервера
# self.assertEqual(A, B) - проверяет, что А=В response.status_code - код ответа сервера
# self.assertRedirects(ответ, адрес) - проверяет куда ведет редирект
#User.objects.filter(username='newstudent') — ищет пользователя с логином newstudent; .exists() — возвращает True, если нашли, False — если нет; self.assertTrue() — проверяет, что результат равен True


class AuthTests(TestCase):
    #регистрация ученика
    def test_1_register_student_success(self):
        response = self.client.post('/register/', { 
            'username': 'newstudent',
            'first_name': 'Михаил',
            'last_name': 'Семенов',
            'password': 'Student123',
            'role': 'student'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/student/dashboard/')
        self.assertTrue(User.objects.filter(username='newstudent').exists())
        user = User.objects.get(username='newstudent')
        self.assertTrue(user.is_student)
        self.assertFalse(user.is_teacher)
    #регистрация репетитора
    def test_2_register_teacher_success(self):
        response = self.client.post('/register/', {
            'username': 'newteacher',
            'first_name': 'Мария',
            'last_name': 'Иванова',
            'password': 'Teacher123',
            'role': 'teacher'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/teacher/dashboard/')
        self.assertTrue(User.objects.filter(username='newteacher').exists())
        user = User.objects.get(username='newteacher')
        self.assertTrue(user.is_teacher)
        self.assertFalse(user.is_student)

    #регистрация с существующим логином 
    def test_3_register_duplicate_username(self):    
        User.objects.create_user(username='existinguser', password='pass123')
        response = self.client.post('/register/', {
            'username': 'existinguser',
            'first_name': 'Другой',
            'last_name': 'Пользователь',
            'password': 'Pass123',
            'role': 'student'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(username='existinguser').count(), 1)
        self.assertContains(response, 'A user with that username already exists')

    #вход ученика
    def test_4_login_student_success(self):
        #создаем ученика и сохраняем
        user = User.objects.create_user(username='loginstudent', password='StudentPass123')
        user.is_student = True
        user.save()
        response = self.client.post('/login/', {
            'username': 'loginstudent',
            'password': 'StudentPass123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/student/dashboard/')
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    #вход репетитора
    def test_5_login_teacher_success(self):
        user = User.objects.create_user(username='loginteacher', password='TeacherPass123')
        user.is_teacher = True
        user.save()
        response = self.client.post('/login/', {
            'username': 'loginteacher',
            'password': 'TeacherPass123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/teacher/dashboard/')

    #вход с неправильным паролем
    def test_6_login_wrong_password(self):
        User.objects.create_user(username='wronguser', password='RealPass123')
        response = self.client.post('/login/', {
            'username': 'wronguser',
            'password': 'WrongPass456'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Неверное имя пользователя или пароль')
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    #доступ без авторизации
    def test_7_student_dashboard_requires_login(self):
        response = self.client.get('/student/dashboard/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))

    #доступ без авторизации
    def test_8_teacher_dashboard_requires_login(self):
        response = self.client.get('/teacher/dashboard/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))

    #выход
    def test_9_logout(self):
        user = User.objects.create_user(username='logoutuser', password='pass123')
        self.client.login(username='logoutuser', password='pass123')
        response = self.client.post('/logout/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/')
        self.assertFalse(response.wsgi_request.user.is_authenticated)