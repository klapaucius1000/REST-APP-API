"""
Tests for tags API
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag,Book

from book.serializers import TagSerializer

TAGS_URL = reverse('book:tag-list')


def detail_url(tag_id):
    """Create and return a tag detail url."""
    return reverse('book:tag-detail', args=[tag_id])


def create_user(email='user@example.com', password='test123'):
    """Create a return a new user."""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicTagsApiTests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test authenticate is required for retrieving tags."""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test  for retrieving a list of tags."""
        Tag.objects.create(user=self.user, name='Book of the year')
        Tag.objects.create(user=self.user, name='Ill read it again sometime')

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test display tags only for the authenticated user"""
        user2 = create_user(email='user2@user2.com')
        Tag.objects.create(user=user2, name='Example')
        tag = Tag.objects.create(user=self.user, name='Another Example')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'], tag.id)

    def test_update_tag(self):
        """Test updating a tag."""
        tag = Tag.objects.create(user=self.user, name='Example three')

        payload = {'name': 'Tag Title'}
        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag(self):
        """Test deleting a tag."""
        tag = Tag.objects.create(user=self.user, name='Example four')

        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())

    def test_filter_tags_assigned_to_books(self):
        """Test summary of tags of books assigned to it."""
        tag1 = Tag.objects.create(user=self.user, name='Funny')
        tag2 = Tag.objects.create(user=self.user, name='Not Funny')
        book = Book.objects.create(
            author='Tymon Grabowski',
            title='Grzybologika',
            category='Essay',
            number_of_pages=122,
            language='Polski',
            cost=Decimal('33.33'),
            description='sample description',
            user=self.user,
        )
        book.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)


    def test_filtered_tags_unique(self):
        """Test filtered of tags returns a unique list."""
        tag = Tag.objects.create(user=self.user, name='Funny')
        Tag.objects.create(user=self.user, name='Not Funny')
        book1 = Book.objects.create(
            author='Tymon Grabowski',
            title='Grzybologika',
            category='Essay',
            number_of_pages=122,
            language='Polski',
            cost=Decimal('33.33'),
            description='sample description',
            user=self.user,
        )
        book2 = Book.objects.create(
            author='Tymon Grabowski2',
            title='Grzybologika2',
            category='Essay',
            number_of_pages=112,
            language='Polski',
            cost=Decimal('33.13'),
            description='sample description2',
            user=self.user,
        )
        book1.tags.add(tag)
        book2.tags.add(tag)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)