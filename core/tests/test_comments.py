from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from ..models import Test, Question, Option, Answer, Teacher, Student, Comment

User = get_user_model()

class CommentsBackendTests(TestCase):
    def setUp(self):
        self.teacher_user = User.objects.create_user(
            username='teacher', password='pass123', is_teacher=True
        )
        self.teacher = Teacher.objects.create(user=self.teacher_user)

        self.student_user = User.objects.create_user(
            username='student', password='pass123', is_student=True
        )
        self.student = Student.objects.create(user=self.student_user)

        self.test = Test.objects.create(
            title='Тест для комментариев', description='Описание', teacher=self.teacher_user
        )

        self.question = Question.objects.create(
            test=self.test, text='Сколько будет 2+2?', question_type='single', points=1
        )

        self.option = Option.objects.create(question=self.question, text='4', is_correct=True)

        self.answer = Answer.objects.create(
            student=self.student_user, test=self.test, question=self.question,
            selected_option=self.option, is_correct=False
        )

    #учитель имеет доступ к списку ответов на проверку
    def test_teacher_can_access_pending_answers(self):
        self.client.login(username='teacher', password='pass123')
        response = self.client.get(reverse('pending_answers'))
        self.assertEqual(response.status_code, 200)

    #ученик не имеет доступа к странице проверки ответов
    def test_student_cannot_access_pending_answers(self):
        self.client.login(username='student', password='pass123')
        response = self.client.get(reverse('pending_answers'))
        self.assertEqual(response.status_code, 302)

    #комментарии сохраняются в базе данных
    def test_comment_is_saved_to_database(self):
        self.client.login(username='teacher', password='pass123')
        self.assertEqual(Comment.objects.count(), 0)
        self.client.post(
            reverse('add_comment', args=[self.answer.id]),
            {'text': 'Это тестовый комментарий'}
        )
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.first()
        self.assertEqual(comment.text, 'Это тестовый комментарий')
        self.assertEqual(comment.teacher, self.teacher_user)
        self.assertEqual(comment.answer, self.answer)

    #пустой комментарий не сохраняется в БД
    def test_empty_comment_is_not_saved(self):
        self.client.login(username='teacher', password='pass123')
        initial_count = Comment.objects.count()
        self.client.post(
            reverse('add_comment', args=[self.answer.id]),
            {'text': ''}
        )
        self.assertEqual(Comment.objects.count(), initial_count)

    #ученик видит свои комментарии
    def test_student_can_view_his_comments(self):
        self.client.login(username='teacher', password='pass123')
        self.client.post(
            reverse('add_comment', args=[self.answer.id]),
            {'text': 'Комментарий для ученика'}
        )
        self.client.logout()
        self.client.login(username='student', password='pass123')
        response = self.client.get(reverse('my_comments'))
        self.assertEqual(response.status_code, 200)

    #репетитор не имеет доступа к странице комментариев ученика
    def test_teacher_cannot_view_student_comments_page(self):
        self.client.login(username='teacher', password='pass123')
        response = self.client.get(reverse('my_comments'))
        self.assertEqual(response.status_code, 302)  