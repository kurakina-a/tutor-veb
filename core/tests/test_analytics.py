from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from ..models import Test, Question, Option, Answer, Teacher, Student

User = get_user_model()

class AnalyticsTests(TestCase):

    def setUp(self):
        self.teacher_user = User.objects.create_user(
            username='literature_teacher',
            password='pass123',
            is_teacher=True
        )
        self.teacher = Teacher.objects.create(user=self.teacher_user)
        self.client.login(username='literature_teacher', password='pass123')

        self.student_anna = User.objects.create_user(
            username='anna_student', password='pass123', is_student=True
        )
        self.student_peter = User.objects.create_user(
            username='peter_student', password='pass123', is_student=True
        )

        self.test = Test.objects.create(
            title='Евгений Онегин',
            description='Тест по роману А.С. Пушкина',
            teacher=self.teacher_user
        )

        self.q1 = Question.objects.create(
            test=self.test,
            text='Кто написал роман "Евгений Онегин"?',
            question_type='single',
            points=1
        )
        self.q1_correct = Option.objects.create(
            question=self.q1, text='А.С. Пушкин', is_correct=True
        )
        self.q1_wrong = Option.objects.create(
            question=self.q1, text='М.Ю. Лермонтов', is_correct=False
        )

        self.q2 = Question.objects.create(
            test=self.test,
            text='Какие черты характера присущи Евгению Онегину?',
            question_type='multiple',
            points=2
        )
        self.q2_correct1 = Option.objects.create(
            question=self.q2, text='Скептицизм', is_correct=True
        )
        self.q2_correct2 = Option.objects.create(
            question=self.q2, text='Хандра', is_correct=True
        )
        self.q2_wrong1 = Option.objects.create(
            question=self.q2, text='Романтизм', is_correct=False
        )

        self.q3 = Question.objects.create(
            test=self.test,
            text='Почему Онегин отказался от дуэли с Ленским?',
            question_type='text',
            points=3
        )

    #статистика показывает, что вопрос вызывает трудности
    def test_statistics_shows_author_question_mistakes(self):
        Answer.objects.create(
            student=self.student_anna, test=self.test, question=self.q1,
            selected_option=self.q1_wrong, is_correct=False
        )
        Answer.objects.create(
            student=self.student_peter, test=self.test, question=self.q1,
            selected_option=self.q1_correct, is_correct=True
        )
        response = self.client.get(reverse('teacher_statistics'))
        self.assertEqual(response.status_code, 200)
        stats = response.context['stats']
        test_stat = None
        for s in stats:
            if s['title'] == self.test.title:
                test_stat = s
                break
        self.assertIsNotNone(test_stat)
        q1_stat = None
        for q in test_stat['questions']:
            if q['id'] == self.q1.id:
                q1_stat = q
                break
        self.assertIsNotNone(q1_stat)
        self.assertEqual(q1_stat['total_count'], 2)
        self.assertEqual(q1_stat['wrong_count'], 1)
        self.assertEqual(q1_stat['error_percent'], 50)

    #статистика показывает ошибки в вопросе с множественным выбором
    def test_statistics_shows_multiple_choice_mistakes(self):
        Answer.objects.create(
            student=self.student_anna, test=self.test, question=self.q2,
            selected_option=self.q2_correct1, is_correct=False  
        )
        Answer.objects.create(
            student=self.student_peter, test=self.test, question=self.q2,
            selected_option=self.q2_correct1, is_correct=True
        )
        Answer.objects.create(
            student=self.student_peter, test=self.test, question=self.q2,
            selected_option=self.q2_correct2, is_correct=True
        )
        response = self.client.get(reverse('teacher_statistics'))
        stats = response.context['stats']
        test_stat = next((s for s in stats if s['title'] == self.test.title), None)
        q2_stat = next((q for q in test_stat['questions'] if q['id'] == self.q2.id), None)
        self.assertEqual(q2_stat['total_count'], 3)
        self.assertEqual(q2_stat['wrong_count'], 1)
        self.assertEqual(q2_stat['error_percent'], 33)

    #рекомендации показывают ученнику его слабые места
    def test_recommendations_show_weak_topics(self):
        for _ in range(2):
            Answer.objects.create(
                student=self.student_anna, test=self.test, question=self.q1,
                selected_option=self.q1_wrong, is_correct=False
            )
        Answer.objects.create(
            student=self.student_anna, test=self.test, question=self.q2,
            selected_option=self.q2_correct1, is_correct=True
        )
        Answer.objects.create(
            student=self.student_anna, test=self.test, question=self.q2,
            selected_option=self.q2_correct2, is_correct=True
        )
        self.client.logout()
        self.client.login(username='anna_student', password='pass123')
        response = self.client.get(reverse('my_recommendations'))
        self.assertEqual(response.status_code, 200)
        recommendations = response.context['recommendations']
        self.assertGreaterEqual(len(recommendations), 1)
        self.assertEqual(recommendations[0]['question_text'], self.q1.text)
        self.assertEqual(recommendations[0]['wrong_count'], 2)

    #правильно рассчитывается успеваемость ученика в процентах
    def test_student_success_rate_calculation(self):
        Answer.objects.create(
            student=self.student_anna, test=self.test, question=self.q1,
            selected_option=self.q1_correct, is_correct=True
        )
        Answer.objects.create(
            student=self.student_anna, test=self.test, question=self.q2,
            selected_option=self.q2_correct1, is_correct=True
        )
        Answer.objects.create(
            student=self.student_anna, test=self.test, question=self.q2,
            selected_option=self.q2_correct2, is_correct=True
        )
        for _ in range(2):
            Answer.objects.create(
                student=self.student_anna, test=self.test, question=self.q1,
                selected_option=self.q1_wrong, is_correct=False
            )
        self.client.logout()
        self.client.login(username='anna_student', password='pass123')
        response = self.client.get(reverse('my_recommendations'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_answers'], 5)
        self.assertEqual(response.context['total_wrong'], 2)
        self.assertEqual(response.context['success_rate'], 60)  

    #статистика выделяет вопрос с наибольшим процентом ошибок
    def test_statistics_identifies_problem_question(self):
        for _ in range(3):
            Answer.objects.create(
                student=self.student_anna, test=self.test, question=self.q1,
                selected_option=self.q1_wrong, is_correct=False
            )
        for i in range(3):
            opt = self.q2_wrong1 if i == 0 else self.q2_correct1
            Answer.objects.create(
                student=self.student_anna, test=self.test, question=self.q2,
                selected_option=opt, is_correct=(i != 0)
            )
        response = self.client.get(reverse('teacher_statistics'))
        stats = response.context['stats']
        test_stat = next((s for s in stats if s['title'] == self.test.title), None)
        max_error_question = max(test_stat['questions'], key=lambda x: x['error_percent'])
        self.assertEqual(max_error_question['id'], self.q1.id)
        self.assertEqual(max_error_question['error_percent'], 100)