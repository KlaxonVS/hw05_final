from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',)
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост1234',)

    def test_models_have_correct_object_names(self):
        """Проверка результата метода __str__ для моделей"""
        post = PostModelTest.post
        expected_post_name = post.text[0:14]
        post_error_text = ('Метод __str__ должен вернуть текс поста '
                           'с ограничением 15 символов')
        group = PostModelTest.group
        expected_group_name = group.title
        group_error_text = 'Метод __str__ должен вернуть тайтл группы'
        test_object_name = {
            post: [expected_post_name, post_error_text],
            group: [expected_group_name, group_error_text]

        }
        for test_obj, (expected_value, error) in test_object_name.items():
            with self.subTest(test_obj=test_obj):
                self.assertEqual(expected_value,
                                 str(test_obj),
                                 error)

    def test_verbose_name(self):
        post = PostModelTest.post
        field_verboses = {
            'text': 'Пост',
            'pub_date': 'Дата публикации',
            'group': 'Группа',
            'author': 'Автор',
            'image': 'Картинка',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(post._meta.get_field(field).verbose_name,
                                 expected_value
                                 )

    def test_help_text(self):
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
            'image': 'Загрузите изображение',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)
