from django.test import TestCase, Client
from django.urls import reverse


class TestAboutURL(TestCase):

    def setUp(self):
        self.client = Client()

    def test_about_urls(self):
        abouts = ('about:author', 'about:tech')
        for about in abouts:
            with self.subTest(about=about):
                response = self.client.get(reverse(about))
                self.assertEqual(response.reason_phrase, 'OK')

    def test_used_template(self):
        templates = (
            ('about:author', 'about/basic_about.html'),
            ('about:tech', 'about/basic_about.html'),
        )
        for address, template in templates:
            with self.subTest(address=address):
                response = self.client.get(reverse(address))
                self.assertTemplateUsed(response, template)

    def test_reverse(self):
        reverses = (
            ('about:author', '/about/author/'),
            ('about:tech', '/about/tech/'),
        )
        for revers, url in reverses:
            with self.subTest(revers=revers):
                self.assertEqual(reverse(revers), url)
