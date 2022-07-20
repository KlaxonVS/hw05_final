import shutil
from tempfile import mkdtemp

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms

from ..forms import PostForm
from ..models import Group, Post, Comment, Follow

User = get_user_model()
POSTS_LMT = settings.POSTS_ON_PAGE_LMT
Q_OF_POSTS = 15
PAGE_LEFTOVERS = 5
TEST_DIR = mkdtemp()


@override_settings(MEDIA_ROOT=TEST_DIR,)
class TestPostViews(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(
            username='test_user',
            first_name='Юзер',
            last_name='Тестовый',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Описание группы'
        )
        test_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        img = SimpleUploadedFile(
            name='test.gif',
            content=test_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text='Тестовый пост',
            image=img,
        )
        cls.comment = Comment.objects.create(
            text='Тестовый комментарий',
            author=cls.author,
            post=cls.post,
        )
        cls.follower = User.objects.create_user(
            username='test_follower',
            first_name='Фолловер',
            last_name='Тестовый',
        )
        cls.follow = Follow.objects.create(
            user=cls.follower,
            author=cls.author
        )
        cls.not_follower = User.objects.create_user(
            username='test_follower2',
            first_name='ФолловерДва',
            last_name='Тестовый',
        )

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)
        self.authorized_client_follower = Client()
        self.authorized_client_follower.force_login(self.follower)
        self.authorized_not_follower = Client()
        self.authorized_not_follower.force_login(self.not_follower)

    def tearDown(self):
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        cache.clear()
        shutil.rmtree(TEST_DIR, ignore_errors=True)
        super().tearDownClass()

    def check_context(self, response, post=False):
        """Проверка context поста"""
        context = (response.context['post']
                   if post else
                   response.context['page_obj'][0])
        self.assertEqual(context.author, self.author)
        self.assertEqual(context.pub_date, self.post.pub_date)
        self.assertEqual(context.text, self.post.text)
        self.assertEqual(context.group, self.post.group)
        self.assertEqual(context.image, self.post.image)
        self.assertContains(response, '<img')

    def test_index_context(self):
        """Проверка context главной страницы"""
        response = self.authorized_author.get(reverse('posts:index'))
        self.check_context(response)

    def test_follow_page_context(self):
        """Проверка context страницы подписок"""
        response = self.authorized_client_follower.get(
            reverse('posts:follow_index')
        )
        self.check_context(response)

    def test_group_list_context(self):
        """Проверка context страницы группы"""
        response = self.authorized_author.get(
            reverse('posts:group_list', args=(self.group.slug,))
        )
        self.check_context(response)
        group_check = response.context['group']
        self.assertEqual(group_check, self.group)

    def test_profile_context(self):
        """Проверка context страницы профиля"""
        response = self.authorized_client_follower.get(
            reverse('posts:profile', args=(self.author.username,))
        )
        self.check_context(response)
        author_check = response.context['author']
        self.assertEqual(author_check, self.author)
        following_check = response.context['following'][0]
        self.assertEqual(following_check, self.follow)
        unauth_response = self.client.get(
            reverse('posts:profile', args=(self.author.username,))
        )
        following_check = unauth_response.context['following']
        self.assertEqual(following_check, False)

    def test_post_detail_context(self):
        """Проверка context страницы поста"""
        response = self.authorized_author.get(
            reverse('posts:post_detail', args=(self.post.id,))
        )
        self.check_context(response, post=True)
        comments_check = response.context['comments'][0]
        self.assertEqual(comments_check, self.comment)

    def test_page_context_with_form(self):
        """
        Проверка context страниц создания и редактированияпоста с формой
        """
        form_fields = (
            ('text', forms.fields.CharField),
            ('group', forms.fields.ChoiceField),
        )
        create_or_edit = (
            ('posts:post_create', None),
            ('posts:post_edit', (self.post.id,)),
        )
        for address, arg in create_or_edit:
            with self.subTest(address=address):
                response = self.authorized_author.get(
                    reverse(address, args=arg)
                )
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], PostForm)
                for value, expected in form_fields:
                    with self.subTest(value=value):
                        field = response.context.get('form').fields.get(value)
                        self.assertIsInstance(field, expected)

    def test_post_in_right_places(self):
        """
        Проверка нахождения постов в соответствующих группах
        """
        self.group2 = Group.objects.create(title='Тестовая группа 2',
                                           slug='test-slug2',)
        self.post2 = Post.objects.create(author=self.author,
                                         group=self.group,
                                         text='Тестовый пост 2',)
        response_group = self.authorized_author.get(
            reverse('posts:group_list', args=(self.group.slug,))
        )
        response_group2 = self.authorized_author.get(
            reverse('posts:group_list', args=(self.group2.slug,))
        )
        self.assertEqual(len(response_group2.context['page_obj']), 0)
        self.assertIn(self.post2, response_group.context['page_obj'])
        self.assertEqual(self.post2.group, self.group)

    def test_follow_in_right_places(self):
        """
        Новый пост созданным автором в подписках
        отображается на странице подписок
        """
        new_post = {'text': 'Новый пост', }
        self.authorized_author.post(
            reverse('posts:post_create'),
            new_post
        )
        new_post = Post.objects.first()
        follower_response = self.authorized_client_follower.get(
            reverse('posts:follow_index')
        )
        self.assertIn(new_post, follower_response.context['page_obj'])
        not_follower_response = self.authorized_not_follower.get(
            reverse('posts:follow_index')
        )
        self.assertNotIn(new_post, not_follower_response.context['page_obj'])

    def test_follow(self):
        """Проверка создания подписки"""
        follow_count = Follow.objects.count()
        follow = self.authorized_not_follower.get(
            reverse('posts:profile_follow', args=(self.author.username,))
        )
        self.assertRedirects(
            follow,
            reverse('posts:profile', args=(self.author.username,))
        )
        follow_page = self.authorized_not_follower.get(
            reverse('posts:follow_index'),
        )
        self.assertIn(self.post, follow_page.context['page_obj'])
        follow_count2 = Follow.objects.count()
        self.assertEqual(follow_count2, follow_count + 1)
        follow = Follow.objects.last()
        self.assertEqual(self.not_follower, follow.user)
        self.assertEqual(self.author, follow.author)

    def test_unfollow(self):
        """Проверка удаления подписки"""
        follow_count = Follow.objects.count()
        unfollow = self.authorized_client_follower.get(
            reverse('posts:profile_unfollow', args=(self.author.username,))
        )
        self.assertRedirects(
            unfollow,
            reverse('posts:profile', args=(self.author.username,))
        )
        follow_page2 = self.authorized_client_follower.get(
            reverse('posts:follow_index'),
        )
        self.assertNotIn(self.post, follow_page2.context['page_obj'])
        follow_count2 = Follow.objects.count()
        self.assertEqual(follow_count2, follow_count - 1)

    def test_follow_not_twice(self):
        """
        При попытке дважды подписаться на одного авторы
        запись в базе данных не дублируется
        """
        follow_count = Follow.objects.count()
        self.authorized_client_follower.get(
            reverse('posts:profile_follow', args=(self.author.username,))
        )
        follow_count2 = Follow.objects.count()
        self.assertEqual(follow_count, follow_count2)

    def test_self_follow(self):
        """Проверка, что нельзя подписаться на самого себя"""
        follow_count = Follow.objects.count()
        self.authorized_author.get(
            reverse('posts:profile_follow', args=(self.author.username,))
        )
        follow_count2 = Follow.objects.count()
        self.assertEqual(follow_count, follow_count2)

    def test_cash(self):
        """Проверка работы кэша главной страницы"""
        new_post = {'text': 'Проверка кэша', }
        self.authorized_author.post(
            reverse('posts:post_create'),
            new_post
        )
        post2 = Post.objects.first()
        response1 = self.client.get(reverse('posts:index'))
        response_1 = response1.content
        post2.delete()
        response2 = self.client.get(reverse('posts:index'))
        response_2 = response2.content
        self.assertEqual(response_1, response_2)
        cache.clear()
        response3 = self.client.get(reverse('posts:index'))
        response_3 = response3.content
        self.assertNotEqual(response_1, response_3)


class PaginatorViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(title='Test group', slug='test-group')
        cls.author = User.objects.create(username='test_author')
        test_post_list = []
        for post in range(Q_OF_POSTS):
            test_post_list.append(
                Post.objects.create(text=f'Text {post}',
                                    group=cls.group,
                                    author=cls.author,)
            )
        cls.follower = User.objects.create_user(
            username='test_follower',
            first_name='Фолловер',
            last_name='Тестовый',
        )
        cls.follow = Follow.objects.create(
            user=cls.follower,
            author=cls.author
        )
        cls.authorized_client_follower = Client()
        cls.authorized_client_follower.force_login(cls.follower)

    def test_page_contains_records(self):
        """
        Проверка работы пагинатора
        и на странице правильно работает ограничение записей
        """
        pages_to_test = (
            ('posts:index', None),
            ('posts:follow_index', None),
            ('posts:group_list', (self.group.slug,)),
            ('posts:profile', (self.author.username,)),
        )
        for page, arg in pages_to_test:
            with self.subTest(page=page):
                pages = (
                    ('?page=1', POSTS_LMT),
                    ('?page=2', PAGE_LEFTOVERS)
                )
                for specific_page, posts in pages:
                    with self.subTest(specific_page=specific_page):
                        response = self.authorized_client_follower.get(
                            reverse(page, args=arg) + specific_page
                        )
                        self.assertEqual(
                            len(response.context['page_obj']),
                            posts
                        )
