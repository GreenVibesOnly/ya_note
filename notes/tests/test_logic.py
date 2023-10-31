from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.models import Note


User = get_user_model()


class TestNoteCreation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.add_url = reverse('notes:add')
        cls.login_url = reverse('users:login')
        cls.author = User.objects.create(username='Джон Толкин')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author
        )
        cls.form_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': 'new_slug'
        }

    # Создание заметки авторизованным пользователем
    def test_user_can_create_note(self):
        count_notes_before = Note.objects.count()
        response = self.author_client.post(self.add_url, data=self.form_data)
        # Проверка редиректа
        self.assertRedirects(response, reverse('notes:success'))
        count_notes_after = Note.objects.count()
        # Заметка создалась
        self.assertEqual(count_notes_before + 1, count_notes_after)
        new_note = Note.objects.last()
        # Проверка соответствия полей заметки
        self.assertEqual(new_note.title, self.form_data['title'])
        self.assertEqual(new_note.text, self.form_data['text'])
        self.assertEqual(new_note.slug, self.form_data['slug'])
        self.assertEqual(new_note.author, self.author)

    # Неавторизованный пользователь не может создать заметку
    def test_anonymous_user_cant_create_note(self):
        count_notes_before = Note.objects.count()
        response = self.client.post(self.add_url, data=self.form_data)
        expected_url = f'{self.login_url}?next={self.add_url}'
        # Проверка редиректа
        self.assertRedirects(response, expected_url)
        count_notes_after = Note.objects.count()
        # Заметка не создалась
        self.assertEqual(count_notes_before, count_notes_after)

    # Заметка с существующим слагом не создается
    def test_not_unique_slug(self):
        count_notes_before = Note.objects.count()
        self.form_data['slug'] = self.note.slug
        self.author_client.post(self.add_url, data=self.form_data)
        count_notes_after = Note.objects.count()
        # Заметка не создалась
        self.assertEqual(count_notes_before, count_notes_after)

    # Автоматическое создание слага
    def test_empty_slug(self):
        count_notes_before = Note.objects.count()
        self.form_data.pop('slug')
        response = self.author_client.post(self.add_url, data=self.form_data)
        # Проверка успешного редиректа:
        self.assertRedirects(response, reverse('notes:success'))
        count_notes_after = Note.objects.count()
        # Заметка создалась:
        self.assertEqual(count_notes_before + 1, count_notes_after)
        expected_slug = slugify(self.form_data['title'])
        # Слаг создался ожидаемым образом:
        self.assertEqual(Note.objects.last().slug, expected_slug)


class TestNoteEditDelete(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Джон Толкин')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Бильбо Бэггинс')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author
        )
        cls.form_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': 'new_slug'
        }
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))

    # Автор может удалить заметку
    def test_author_can_delete_note(self):
        response = self.author_client.delete(self.delete_url)
        # Проверка успешного редиректа:
        self.assertRedirects(response, reverse('notes:success'))
        # Заметка далилась:
        self.assertEqual(Note.objects.count(), 0)

    # Пользователь не может удалить чужую заметку
    def test_user_cant_delete_comment_of_another_user(self):
        response = self.reader_client.delete(self.delete_url)
        # Страница недоступна:
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Заметка не удалилась:
        self.assertEqual(Note.objects.count(), 1)

    # Автор может редактировать заметку
    def test_author_can_edit_note(self):
        response = self.author_client.post(self.edit_url, data=self.form_data)
        # Проверка успешного редиректа:
        self.assertRedirects(response, reverse('notes:success'))
        self.note.refresh_from_db()
        # Заметка изменилась:
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.slug, self.form_data['slug'])

    # Пользователь не может редактировать чужую заметку
    def test_user_cant_edit_comment_of_another_user(self):
        note_id = self.note.id
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        # Страница недоступна:
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_from_db = Note.objects.get(id=note_id)
        # Заметка не изменилась:
        self.assertEqual(self.note.title, note_from_db.title)
        self.assertEqual(self.note.text, note_from_db.text)
        self.assertEqual(self.note.slug, note_from_db.slug)
