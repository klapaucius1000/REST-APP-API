"""
Test for models.
"""
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


class ModelTests(TestCase):
	"""Test for models"""

	def test_create_user_with_email_successful(self):
		""" Test creating user with an email is successful."""
		email = "test@example.com"
		password = 'testpass123'
		user = get_user_model().objects.create_user(
			email=email,
			password=password,
		)

		self.assertEqual(user.email, email)
		self.assertTrue(user.check_password(password))

	def test_new_user_email_normalized(self):
		"""Test email is normalized for new users."""

		sample_emails = [
			['test1@EXAMPLE.com', 'test1@example.com'],
			['Test2@Example.com', 'Test2@example.com'],
			['TEST3@EXAMPLE.com', 'TEST3@example.com'],
			['test4@example.COM', 'test4@example.com'],
		]
		for email, expected in sample_emails:
			user = get_user_model().objects.create_user(email, 'sample123')
			self.assertEqual(user.email, expected)

	def test_new_user_without_email_raises_error(self):
		"""Test  creating a user without an email raises a ValueError."""
		with self.assertRaises(ValueError):
			get_user_model().objects.create_user('', 'sample123')

	def test_create_superuser(self):
		"""Test for creating a superuser"""
		user = get_user_model().objects.create_superuser(
			'test@example.com',
			'sample123',
		)

		self.assertTrue(user.is_superuser)
		self.assertTrue(user.is_staff)

	def test_create_book(self):
		""" Test creating new book is successful."""
		user = get_user_model().objects.create_user(
			'test@example.com',
			'sample123',
		)
		book = models.Book.objects.create(
			user=user,
			author='Joe Doe',
			title='Sample title',
			category='Drama',
			number_of_pages=121,
			language='Hindi',
			cost=Decimal('5.50'),
			description='sample description'
		)

		self.assertEqual(str(book), book.title)