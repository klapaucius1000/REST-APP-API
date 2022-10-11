""" Test for books APIs."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Book

from book.serializers import BookSerializer, BookDetailSerializer

BOOKS_URL = reverse('book:book-list')


def detail_url(book_id):
    """Create and return a book detail URL."""
    return reverse('book:book-detail', args=[book_id])


def test_get_book_detail(self):
    """Test get book detail."""
    book = create_book(user=self.user)

    url = detail_url(book.id)
    res = self.client.get(url)
    serializer = BookDetailSerializer(book)
    self.assertEqual(res.data, serializer.data)


def create_book(user, **params):
    """ Create and return a sample entry, record"""
    defaults = {
        'title': 'Sample  entry',
        'author': 'Johny Bravo',
        'category': 'Drama',
        'number_of_pages': 121,
        'language': 'Hindi',
        'cost': Decimal('5.50'),
        'description': 'sample description',
        'link': 'http://example.com/entry.pdf',
    }
    defaults.update(params)

    book = Book.objects.create(user=user, **defaults)
    return book


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicBookAPITests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""
        res = self.client.get(BOOKS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateBookAPITests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test@example.com',
            'sample123',
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_books(self):
        """ Test retrieving a list of books."""
        create_book(user=self.user)
        create_book(user=self.user)

        res = self.client.get(BOOKS_URL)

        books = Book.objects.all().order_by('-id')
        serializer = BookSerializer(books, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_book_list_limited_to_user(self):
        """ Test list of book is limited to auth user."""
        other_user = get_user_model().objects.create_user(
            email='another@example.com',
            password='sample1232',
        )

        create_book(user=other_user)
        create_book(user=self.user)

        res = self.client.get(BOOKS_URL)

        books = Book.objects.filter(user=self.user)
        serializer = BookSerializer(books, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_book_detail(self):
        """Test get book detail."""
        book = create_book(user=self.user)

        url = detail_url(book.id)
        res = self.client.get(url)

        serializer = BookDetailSerializer(book)
        self.assertEqual(res.data, serializer.data)

    def test_partial_update(self):
        """Test partial update of entry."""
        original_link = "https://example.com/book.pdf"
        book = create_book(
            user=self.user,
            title='sample title',
            link=original_link

        )
        payload = {'title': 'New entry title'}
        url = detail_url(book.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        book.refresh_from_db()
        self.assertEqual(book.title, payload['title'])
        self.assertEqual(book.link, original_link)
        self.assertEqual(book.user, self.user)

    def test_full_update(self):
        """Test full update of entry."""
        book = create_book(
            user=self.user,
            title='Sample book title',
            link='https://exmaple.com/book.pdf',
            description='Sample description.',
        )

        payload = {
            'title': 'New  title',
            'link': 'https://example.com/new-book.pdf',
            'description': 'New book description',
            'author': 'Joe Doe',
            'category': 'Drama',
            'number_of_pages': 121,
            'language': 'Hindi',
            'cost': Decimal('5.50'),

        }
        url = detail_url(book.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        book.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(book, k), v)
        self.assertEqual(book.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the results in an error."""
        new_user = create_user(email='anotheruser@example.com', password='anothertest123')
        book = create_book(user=self.user)

        payload = {'user': new_user.id}
        url = detail_url(book.id)
        self.client.patch(url, payload)

        book.refresh_from_db()
        self.assertEqual(book.user, self.user)

    def test_delete_book(self):
        """Test deleting a book successful."""
        book = create_book(user=self.user)

        url = detail_url(book.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Book.objects.filter(id=book.id).exists())

    def test_book_other_users_book_error(self):
        """Test trying to delete another users book gives error."""
        new_user = create_user(email='anotheruser@example.com', password='anothertest123')
        book = create_book(user=new_user)

        url = detail_url(book.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Book.objects.filter(id=book.id).exists())
