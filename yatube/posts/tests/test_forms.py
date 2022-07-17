from os.path import basename
import shutil
from tempfile import mkdtemp

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from http import HTTPStatus

from ..forms import PostForm, CommentForm
from ..models import Group, Post, Comment

User = get_user_model()
TEST_DIR = mkdtemp()


@override_settings(MEDIA_ROOT=TEST_DIR)
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = PostForm()
        cls.author = User.objects.create_user(
            username='test_author',)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Оригинальный пост',
            group=cls.group,)

    def setUp(self):
        settings.MEDIA_ROOT = mkdtemp()
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_DIR, ignore_errors=True)
        super().tearDownClass()

    def test_labels(self):
        labels = {
            'text': 'Текст поста',
            'group': 'Группа',
            'image': 'Изображение',
        }
        for label, label_text in labels.items():
            with self.subTest(label=label):
                response_label = self.form.fields[label].label
                self.assertEquals(response_label, label_text)

    def test_post_create(self):
        post_count = Post.objects.count()
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
        form_data = {
            'text': 'Тестовый пост',
            'group': self.group.id,
            'image': img,
        }
        response = self.authorized_author.post(
            reverse('posts:post_create'),
            data=form_data,
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertRedirects(
            response,
            reverse('posts:profile', args=(self.author.username,)),
        )
        new_post = Post.objects.first()
        self.assertEqual(
            new_post.author,
            self.author
        )
        self.assertEqual(
            new_post.group,
            self.group
        )
        self.assertEqual(
            new_post.text,
            form_data['text']
        )
        self.assertEqual(
            basename(new_post.image.file.name),
            form_data['image'].name
        )
        group_response = self.authorized_author.get(
            reverse(
                'posts:group_list',
                args=(self.group.slug,))
        )
        self.assertIn(Post.objects.first(), group_response.context['page_obj'])

    def test_post_edit(self):
        post_count = Post.objects.count()
        self.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug2'
        )
        form_data = {'text': 'New text', 'group': self.group2.id}
        response = self.authorized_author.post(
            reverse('posts:post_edit', args=(self.post.id,)),
            form_data,
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', args=(self.post.id,))
        )
        post = Post.objects.first()
        self.assertEqual(
            post.author,
            self.author
        )
        self.assertEqual(post.group, self.group2)
        self.assertEqual(post.text, form_data['text'])
        group_response = self.authorized_author.get(
            reverse('posts:group_list', args=(self.group.slug,))
        )
        self.assertEqual(group_response.status_code, HTTPStatus.OK)
        self.assertNotIn(self.post, group_response.context['page_obj'])
        post_count2 = Post.objects.count()
        self.assertEqual(post_count2, post_count)

    def test_post_create_guest(self):
        post_count = Post.objects.count()
        form_data = {'text': 'Тестовый пост', 'group': self.group.id, }
        response = self.client.post(
            reverse('posts:post_create'),
            form_data
        )
        self.assertRedirects(
            response, reverse('users:login',) + '?next=/create/'
        )
        post_count2 = Post.objects.count()
        self.assertEqual(post_count2, post_count)

    def test_comment_create_guest(self):
        comment_count = Comment.objects.count()
        form_data = {'text': 'Тестовый коментарий',}
        response = self.client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            form_data
        )
        self.assertRedirects(
            response,
            reverse('users:login',)
            + f'?next=/posts/{self.post.id}/comment/'
        )
        comment_count2 = Comment.objects.count()
        self.assertEqual(comment_count2, comment_count)

    def test_comment_create(self):
        comment_count = Comment.objects.count()
        form_data = {'text': 'Новый коментарий'}
        response = self.authorized_author.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            form_data
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', args=(self.post.id,)),
        )
        new_comment = Comment.objects.filter(post=self.post).first()
        self.assertEqual(
            new_comment.author,
            self.author
        )
        self.assertEqual(
            new_comment.text,
            form_data['text']
        )
