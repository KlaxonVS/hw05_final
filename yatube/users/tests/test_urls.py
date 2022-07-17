from django.contrib.auth import get_user_model
from django.test import TestCase, Client

User = get_user_model()

# Поработаю над этим после сдачи обязательной части


class UsersUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user',
                                            email='test@test.com',
                                            password='testpassword1'
                                            )

    def setUp(self):
        self.unauthorized_client = Client()
        self.authorized_client = Client()
        self.authorized_client.login(username='test_user',
                                     password='testpassword1'
                                     )

    def test_url_for_unauthorized_client(self):
        response = self.unauthorized_client.get('/auth/signup/')
        self.assertEqual(response.reason_phrase, 'OK')
        response = self.unauthorized_client.get('/auth/login/')
        self.assertEqual(response.reason_phrase, 'OK')
        response = self.unauthorized_client.get('/auth/password_reset/')
        self.assertEqual(response.reason_phrase, 'OK')

    def test_login(self):
        response = self.unauthorized_client.post(
            '/auth/login/',
            {'username': 'test_user',
             'password': 'testpassword1'
             }
        )
        self.assertRedirects(response, '/')

    def test_logout(self):
        response = self.authorized_client.get('/auth/logout/')
        self.assertEqual(response.reason_phrase, 'OK')

    def test_password_change(self):
        response = self.authorized_client.post(
            '/auth/password_change/',
            {'old_password': 'testpassword1',
             'new_password1': 'testpassword2',
             'new_password2': 'testpassword2'
             },
        )
        self.assertRedirects(response, '/auth/password_change/done/')

    def test_password_reset(self):
        response = self.unauthorized_client.post(
            '/auth/password_reset/',
            {'email': 'test@test.com'},
        )
        self.assertRedirects(response, '/auth/password_reset/done/')
