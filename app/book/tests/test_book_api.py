""" Test for recipe APIs."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Book

from book.serializers import BookSerializer

BOOKS_URL = reverse('book:book-list')


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
			'another@example.com',
			'sample1232',
		)

		create_book(user=other_user)
		create_book(user=self.user)

		res = self.client.get(BOOKS_URL)

		books = Book.objects.filter(user=self.user)
		serializer = BookSerializer(books, many=True)
		self.assertEqual(res.status_code, status.HTTP_200_OK)
		self.assertEqual(res.data, serializer.data)
