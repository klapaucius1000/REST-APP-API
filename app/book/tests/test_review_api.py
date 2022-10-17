"""
Tests for the reviews API.
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Review

from book.serializers import ReviewSerializer

REVIEWS_URL = reverse('book:review-list')


def detail_url(review_id):
    """Create and return an review detail URL."""
    return reverse('book:review-detail', args=[review_id])


def create_user(email='user@example.com', password='test123'):
    """Create and return user."""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicReviewsApiTests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving reviews."""
        res = self.client.get(REVIEWS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateReviewsApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_reviews(self):
        """Test retrieving a list of reviews."""
        Review.objects.create(user=self.user, name='Example1')
        Review.objects.create(user=self.user, name='Example2')

        res = self.client.get(REVIEWS_URL)

        reviews = Review.objects.all().order_by('-name')
        serializer = ReviewSerializer(reviews, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_reviews_limited_to_user(self):
        """Test list of reviews is limited to authenticated user."""
        user2 = create_user(email='user2@example.com')
        Review.objects.create(user=user2, name='Example3')
        review = Review.objects.create(user=self.user, name='Example4')

        res = self.client.get(REVIEWS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], review.name)
        self.assertEqual(res.data[0]['id'], review.id)

    def test_update_review(self):
        """Test updating a review."""
        review = Review.objects.create(user=self.user, name='Same review')

        payload = {'name': 'Same review2'}
        url = detail_url(review.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        review.refresh_from_db()
        self.assertEqual(review.name, payload['name'])

    def test_delete_review(self):
        """Test deleting a review."""
        review = Review.objects.create(user=self.user, name='Same review3')

        url = detail_url(review.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        reviews = Review.objects.filter(user=self.user)
        self.assertFalse(reviews.exists())
