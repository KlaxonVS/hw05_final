from django.contrib.auth import get_user_model
from django.core.cache import cache

from django.test import TestCase, Client
from django.urls import reverse
from http import HTTPStatus

from ..models import Post, Group

User = get_user_model()


class PostUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',)
        cls.post = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text='Тестовый пост',)

    def setUp(self):
        self.user = User.objects.create_user(username='NoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)
        self.pages = (
            ('posts:index', None),
            ('posts:group_list', (self.group.slug,)),
            ('posts:profile', (self.author.username,)),
            ('posts:post_detail', (self.post.id,)),
            ('posts:post_edit', (self.post.id,)),
            ('posts:post_create', None),
            ('posts:add_comment', (self.post.id,)),
            ('posts:follow_index', None),
            ('posts:profile_follow', (self.author.username,)),
            ('posts:profile_unfollow', (self.author.username,)),
        )

    def tearDown(self):
        cache.clear()

    def test_reverse(self):
        """
        Проверка работы функции reverse():
        соответствия имени приложения и имён пути отображаемому адресу
        """
        reverses = (
            ('posts:index', None, '/'),
            ('posts:group_list', (self.group.slug,),
             f'/group/{self.group.slug}/'),
            ('posts:profile', (self.author.username,),
             f'/profile/{self.author.username}/'),
            ('posts:post_detail', (self.post.id,),
             f'/posts/{self.post.id}/'),
            ('posts:post_edit', (self.post.id,),
             f'/posts/{self.post.id}/edit/'),
            ('posts:post_create', None,
             '/create/',),
            ('posts:add_comment', (self.post.id,),
             f'/posts/{self.post.id}/comment/'),
            ('posts:follow_index', None, '/follow/'),
            ('posts:profile_follow',
             (self.author.username,),
             f'/profile/{self.author.username}/follow/'),
            ('posts:profile_unfollow',
             (self.author.username,),
             f'/profile/{self.author.username}/unfollow/'),
        )
        for revers, arg, url in reverses:
            with self.subTest(revers=revers):
                self.assertEqual(reverse(revers, args=arg), url)

    def test_404(self):
        """
        Проверка, что при попытке перейти на несуществующую страницу,
        пользователь получает страницу со статус кодом 404
        """
        users = (self.client,
                 self.authorized_client,
                 self.authorized_author,)
        for user in users:
            with self.subTest(user=user):
                response = user.get('/unexisting_page/')
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_url_access_for_guest(self):
        """
        Проверка доступа к страницам неавторизованным пользователем
        """
        for page, arg in self.pages:
            with self.subTest(page=page):
                if page in [
                    'posts:post_create',
                    'posts:post_edit',
                    'posts:add_comment',
                    'posts:follow_index',
                    'posts:profile_follow',
                    'posts:profile_unfollow',
                ]:
                    target_page = reverse(page, args=arg)
                    response = self.client.get(
                        target_page,
                        follow=True
                    )
                    login = reverse('users:login',)
                    self.assertRedirects(
                        response,
                        f'{login}?next={target_page}'
                    )
                else:
                    response = self.client.get(
                        reverse(page, args=arg),
                    )
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_access_for_authorized(self):
        """
        Проверка доступа к страницам авторизованным пользователем
        """
        for page, arg in self.pages:
            with self.subTest(page=page):
                if page == 'posts:add_comment':
                    form_data = {'text': 'Новый коментарий'}
                    response = self.authorized_client.post(
                        reverse('posts:add_comment', args=(self.post.id,)),
                        form_data
                    )
                    self.assertRedirects(
                        response,
                        reverse('posts:post_detail', args=(self.post.id,))
                    )
                elif page == 'posts:post_edit':
                    response = self.authorized_client.get(
                        reverse(page, args=arg),
                        follow=True
                    )
                    self.assertRedirects(
                        response,
                        reverse('posts:post_detail', args=(self.post.id,))
                    )
                elif page in [
                    'posts:profile_follow',
                    'posts:profile_unfollow',
                ]:
                    response = self.authorized_client.get(
                        reverse(page, args=arg),
                        follow=True
                    )
                    self.assertRedirects(
                        response,
                        reverse('posts:profile', args=(self.author.username,))
                    )
                else:
                    response = self.authorized_client.get(
                        reverse(page, args=arg)
                    )
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_access_for_author(self):
        """
        Проверка доступа к страницам авторизованным пользователем,
        который является автором поста
        """
        for page, arg in self.pages:
            with self.subTest(page=page):
                if page == 'posts:add_comment':
                    form_data = {'text': 'Новый коментарий'}
                    response = self.authorized_author.post(
                        reverse('posts:add_comment', args=(self.post.id,)),
                        form_data
                    )
                    self.assertRedirects(
                        response,
                        reverse('posts:post_detail', args=(self.post.id,))
                    )
                elif page in [
                    'posts:profile_follow',
                    'posts:profile_unfollow',
                ]:
                    response = self.authorized_client.get(
                        reverse(page, args=arg),
                        follow=True
                    )
                    self.assertRedirects(
                        response,
                        reverse('posts:profile', args=(self.author.username,))
                    )
                else:
                    response = self.authorized_author.get(reverse(page, args=arg))
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_used_template(self):
        """Проверка соответствия шаблона используемого страницей"""
        templates = (
            ('posts:index', None, 'posts/index.html'),
            ('posts:group_list', (self.group.slug,), 'posts/group_list.html'),
            ('posts:profile', (self.author.username,), 'posts/profile.html'),
            ('posts:post_detail', (self.post.id,), 'posts/post_detail.html'),
            ('posts:post_edit', (self.post.id,), 'posts/create_post.html'),
            ('posts:post_create', None, 'posts/create_post.html'),
            ('posts:follow_index', None, 'posts/follow.html'),
        )
        for address, arg, template in templates:
            with self.subTest(address=address):
                response = self.authorized_author.get(
                    reverse(address, args=arg)
                )
                self.assertTemplateUsed(response, template)
