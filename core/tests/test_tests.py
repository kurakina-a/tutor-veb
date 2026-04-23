from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from ..models import Test, Question, Option

User = get_user_model()

class TestModuleTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user( 
            username='teacher',
            password='pass123',
            is_teacher=True
        )
        self.client.login(username='teacher', password='pass123')

    #создание теста
    def test_1_create_test(self):
        response = self.client.post('/tests/create/', {
            'title': 'Роман "Евгений Онегин"',
            'description': 'Тест по роману А.С. Пушкина'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Test.objects.filter(title='Роман "Евгений Онегин"').exists())

    #просмотр списка тестов
    def test_2_test_list(self):
        Test.objects.create(
            title='Роман "Евгений Онегин"',
            description='Тест по роману А.С. Пушкина',
            teacher=self.teacher
        )
        response = self.client.get('/tests/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Роман "Евгений Онегин"')
        self.assertIn('tests', response.context)
        self.assertEqual(response.context['tests'].count(), 1)

    #редактирование теста
    def test_3_edit_test(self):
        test = Test.objects.create(
            title='Роман "Евгений Онегин"',
            description='Тест по роману А.С. Пушкина',
            teacher=self.teacher
        )
        response = self.client.post(f'/tests/{test.id}/edit/', {
            'title': 'Роман "Дубровский"',
            'description': 'Тест по роману А.С. Пушкина'
        })
        self.assertEqual(response.status_code, 302)
        test.refresh_from_db()
        self.assertEqual(test.title, 'Роман "Дубровский"')

    #удаление теста
    def test_4_delete_test(self):
        test = Test.objects.create(
            title='Удаляемый тест',
            description='Описание',
            teacher=self.teacher
        )
        response = self.client.post(f'/tests/{test.id}/delete/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Test.objects.filter(id=test.id).exists())

    #добавление вопроса с выбором одного варианта
    def test_5_add_single_question(self):
        test = Test.objects.create(
            title='Роман "Евгений Онегин"',
            description='Тест по роману А.С. Пушкина',
            teacher=self.teacher
        )
        response = self.client.post(f'/tests/question/add/{test.id}/', {
            'text': 'Кто написал роман "Евгений Онегин"?',
            'question_type': 'single',
            'order': 0
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Question.objects.filter(text='Кто написал роман "Евгений Онегин"?').exists())
        question = Question.objects.first()
        self.assertEqual(question.question_type, 'single')

    #добавление варианта ответа к вопросу
    def test_6_add_option(self):
        test = Test.objects.create(
            title='Роман "Евгений Онегин"',
            description='Тест по роману А.С. Пушкина',
            teacher=self.teacher
        )
        question = Question.objects.create(
            test=test,
            text='Кто написал роман "Евгений Онегин"?',
            question_type='single',
            order=0
        )
        response = self.client.post(f'/question/option/add/{question.id}/', {
            'text': 'А.С. Пушкин',
            'is_correct': True
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Option.objects.filter(text='А.С. Пушкин', is_correct=True).exists())

    #добавление нескольких вариантов (множественный выбор)
    def test_7_add_multiple_options(self):
        test = Test.objects.create(
            title='Произведения Пушкина',
            description='Тест по творчеству А.С. Пушкина',
            teacher=self.teacher
        )
        question = Question.objects.create(
            test=test,
            text='Какие произведения написал Пушкин?',
            question_type='multiple',
            order=0
        )
        response1 = self.client.post(f'/question/option/add/{question.id}/', {
            'text': 'Евгений Онегин',
            'is_correct': True
        })
        response2 = self.client.post(f'/question/option/add/{question.id}/', {
            'text': 'Война и мир',
            'is_correct': False
        })
        response3 = self.client.post(f'/question/option/add/{question.id}/', {
            'text': 'Капитанская дочка',
            'is_correct': True
        })
        self.assertEqual(response1.status_code, 302)
        self.assertEqual(response2.status_code, 302)
        self.assertEqual(response3.status_code, 302)
        
        options = Option.objects.filter(question=question)
        self.assertEqual(options.count(), 3)
        self.assertEqual(options.filter(is_correct=True).count(), 2)

    #редактирование вопроса
    def test_8_edit_question(self):
        test = Test.objects.create(
            title='Роман "Евгений Онегин"',
            description='Тест по роману А.С. Пушкина',
            teacher=self.teacher
        )
        question = Question.objects.create(
            test=test,
            text='Кто написал Евгения Онегина?',
            question_type='single',
            order=0
        )
        response = self.client.post(f'/question/edit/{question.id}/', {
            'text': 'Кто является автором романа "Евгений Онегин"?',
            'question_type': 'single',
            'order': 0
        })
        self.assertEqual(response.status_code, 302)
        question.refresh_from_db()
        self.assertEqual(question.text, 'Кто является автором романа "Евгений Онегин"?')

    #удаление вопроса
    def test_9_delete_question(self):
        test = Test.objects.create(
            title='Роман "Евгений Онегин"',
            description='Тест по роману А.С. Пушкина',
            teacher=self.teacher
        )
        question = Question.objects.create(
            test=test,
            text='Удаляемый вопрос',
            question_type='single',
            order=0
        )
        response = self.client.post(f'/question/delete/{question.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Question.objects.filter(id=question.id).exists())

    #тип вопроса - множественный выбор
    def test_10_question_type_multiple(self):
        test = Test.objects.create(
            title='Литературные произведения',
            description='Тест по литературе',
            teacher=self.teacher
        )
        response = self.client.post(f'/tests/question/add/{test.id}/', {
            'text': 'Какие из этих писателей являются авторами романов?',
            'question_type': 'multiple',
            'order': 0
        })
        self.assertEqual(response.status_code, 302)
        question = Question.objects.first()
        self.assertEqual(question.question_type, 'multiple')

    #тип вопроса - развернутый ответ
    def test_11_question_type_text(self):
        test = Test.objects.create(
            title='Роман "Евгений Онегин"',
            description='Тест по роману А.С. Пушкина',
            teacher=self.teacher
        )
        response = self.client.post(f'/tests/question/add/{test.id}/', {
            'text': 'Проанализируйте образ Татьяны в романе "Евгений Онегин"',
            'question_type': 'text',
            'order': 0
        })
        self.assertEqual(response.status_code, 302)
        question = Question.objects.first()
        self.assertEqual(question.question_type, 'text')
