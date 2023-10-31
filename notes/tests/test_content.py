from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note


User = get_user_model()


class TestContent(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Джон Толкин')
        cls.reader = User.objects.create(username='Бильбо Бэггинс')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author
        )
        cls.note_list_url = reverse('notes:list')

    # Заметка передается на страницу списка заметок
    def test_note_in_author_list(self):
        self.client.force_login(self.author)
        response = self.client.get(self.note_list_url)
        self.assertIn(self.note, response.context['object_list'])

    # Заметка не попадает в список заметок другого пользователя
    def test_note_not_in_reader_list(self):
        self.client.force_login(self.reader)
        response = self.client.get(self.note_list_url)
        self.assertNotIn(self.note, response.context['object_list'])

    # Проверка отображения формы
    def test_pages_contains_form(self):
        self.client.force_login(self.author)
        urls = (
            ('notes:edit', (self.note.slug,)),
            ('notes:add', None)
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertIn('form', response.context)
