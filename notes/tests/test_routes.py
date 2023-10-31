from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from http import HTTPStatus

from notes.models import Note


User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Джон Толкин')
        cls.reader = User.objects.create(username='Бильбо Бэггинс')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author
        )

    # Создание и просмотр заметок для авторизованных
    # и не авторизованных пользователей
    def test_pages_availability(self):
        urls = (
            ('notes:home', self.client),
            ('users:login', self.client),
            ('users:logout', self.client),
            ('users:signup', self.client),
            ('notes:list', self.author),
            ('notes:add', self.author),
            ('notes:success', self.author),
        )
        for name, user in urls:
            if user == self.author:
                self.client.force_login(user)
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    # Доступ к страницам управления заметкой для авторизованных пользователей
    def test_availability_for_comment_edit_and_delete(self):
        users = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in users:
            self.client.force_login(user)
            for name in ('notes:detail', 'notes:edit', 'notes:delete'):
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    # Редирект для анонимных пользователей
    def test_redirect_for_anonymous_client(self):
        login_url = reverse('users:login')
        args = (self.note.slug,)
        urls = (
            ('notes:detail', args),
            ('notes:edit', args),
            ('notes:delete', args),
            ('notes:add', None),
            ('notes:success', None),
            ('notes:list', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
