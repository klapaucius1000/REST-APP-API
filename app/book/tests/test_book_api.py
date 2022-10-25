""" Test for books APIs."""

import tempfile
import os

from PIL import Image
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Book, Tag, Review

from book.serializers import BookSerializer, BookDetailSerializer

BOOKS_URL = reverse('book:book-list')


def detail_url(book_id):
    """Create and return a book detail URL."""
    return reverse('book:book-detail', args=[book_id])


def image_upload_url(book_id):
    """Create and return an image upload URL."""
    return reverse('book:book-upload-image', args=[book_id])


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

    def test_create_book_with_new_tags(self):
        """Test creating a book with new tags."""

        payload = {
            'title': 'Przygody dobrego wojaka Szwejka',
            'author': 'Jaroslav Hasek',
            'description': 'sample',
            'category': 'Novel',
            'number_of_pages': 121,
            'language': 'Cesky',
            'cost': Decimal('15.50'),
            'link': 'https://example.com/new-book.pdf',
            'tags': [{'name': 'Funny'}, {'name': 'read once again'}],
        }
        res = self.client.post(BOOKS_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        books = Book.objects.filter(user=self.user)
        self.assertEqual(books.count(), 1)
        book = books[0]
        self.assertEqual(book.tags.count(), 2)
        for tag in payload['tags']:
            exists = book.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_book_with_exisitng_tags(self):
        """Test creating a book with existing tags."""
        tag_pilipiuk = Tag.objects.create(user=self.user, name='Pilipiuk')
        payload = {
            'author': 'Andrzej Pilipiuk',
            'title': 'Faceci w gumofilcach',
            'category': 'Novel',
            'number_of_pages': 212,
            'language': 'Polski',
            'cost': Decimal('35.50'),
            'description': 'sample description',
            'tags': [{'name': 'Pilipiuk'}, {'name': 'love this'}],
        }
        res = self.client.post(BOOKS_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        books = Book.objects.filter(user=self.user)
        self.assertEqual(books.count(), 1)
        book = books[0]
        self.assertEqual(book.tags.count(), 2)
        self.assertIn(tag_pilipiuk, book.tags.all())
        for tag in payload['tags']:
            exists = book.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test creating tag when update a book."""
        book = create_book(user=self.user)

        payload = {'tags': [{'name': 'Czarnyszewicz'}]}
        url = detail_url(book.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='Czarnyszewicz')
        self.assertIn(new_tag, book.tags.all())

    def test_update_book_assign_tag(self):
        """Test assigning an existing tag when updating a book."""

        tag_taleb = Tag.objects.create(user=self.user, name='Taleb')
        book = create_book(user=self.user)
        book.tags.add(tag_taleb)

        tag_czarnyszewicz = Tag.objects.create(user=self.user, name='Czarnyszewicz')
        payload = {'tags': [{'name': 'Czarnyszewicz'}]}
        url = detail_url(book.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_czarnyszewicz, book.tags.all())
        self.assertNotIn(tag_taleb, book.tags.all())

    def test_clear_book_tags(self):
        """Test clearing a books tags."""
        tag = Tag.objects.create(user=self.user, name='Bieszanow')
        book = create_book(user=self.user)
        book.tags.add(tag)

        payload = {'tags': []}
        url = detail_url(book.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(book.tags.count(), 0)

    def test_create_book_with_new_review(self):
        """Test creating a book with new reviews"""
        payload = {
            'author': 'Tymon Grabowski',
            'title': 'Kuba wyspa gratów',
            'category': 'Reportage',
            'number_of_pages': 212,
            'language': 'Polski',
            'cost': Decimal('33.33'),
            'description': 'sample description',
            'reviews': [{'name': 'some text1'}, {'name': 'some text2'}, {'name': 'some text3'}]
        }
        res = self.client.post(BOOKS_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        books = Book.objects.filter(user=self.user)
        self.assertEqual(books.count(), 1)
        book = books[0]
        self.assertEqual(book.reviews.count(), 3)
        for review in payload['reviews']:
            exists = book.reviews.filter(
                name=review['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_book_with_existing_review(self):
        """Test creating a new book with existing reviews."""
        review = Review.objects.create(user=self.user, name='some text2')
        payload = {
            'author': 'Tymon Grabowski',
            'title': 'Paskudnik warszawski',
            'category': 'Reportage',
            'number_of_pages': 122,
            'language': 'Polski',
            'cost': Decimal('33.33'),
            'description': 'sample description',
            'reviews': [{'name': 'some text1'}, {'name': 'some text2'}, {'name': 'some text3'}]
        }
        res = self.client.post(BOOKS_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        books = Book.objects.filter(user=self.user)
        self.assertEqual(books.count(), 1)
        book = books[0]
        self.assertEqual(book.reviews.count(), 3)
        self.assertIn(review, book.reviews.all())
        for review in payload['reviews']:
            exists = book.reviews.filter(
                name=review['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_review_on_update(self):
        """Test creating a review when updating book."""
        book = create_book(user=self.user)

        payload = {'reviews': [{'name': 'some text4'}]}
        url = detail_url(book.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_review = Review.objects.get(user=self.user, name='some text4')
        self.assertIn(new_review, book.reviews.all())

    def test_update_book_assign_review(self):
        """Test assigning an existing review when updating a book."""
        review1 = Review.objects.create(user=self.user, name='some text5')
        book = create_book(user=self.user)
        book.reviews.add(review1)

        review2 = Review.objects.create(user=self.user, name='some text6')
        payload = {'reviews': [{'name': 'some text6'}]}
        url = detail_url(book.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(review2, book.reviews.all())
        self.assertNotIn(review1, book.reviews.all())

    def test_clear_book_reviews(self):
        """Test clearing a books reviews."""
        review = Review.objects.create(user=self.user, name='some text7')
        book = create_book(user=self.user)
        book.reviews.add(review)

        payload = {'reviews': []}
        url = detail_url(book.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(book.reviews.count(), 0)

    def test_filter_by_tags(self):
        """Filter books by tag Test"""
        book1 = create_book(user=self.user, title='anotherbook1')
        book2 = create_book(user=self.user, title='anotherbook2')
        tag1 = Tag.objects.create(user=self.user, name='funny')
        tag2 = Tag.objects.create(user=self.user, name='not funny')
        book1.tags.add(tag1)
        book2.tags.add(tag2)
        book3 = create_book(user=self.user, title='anotherbook3')

        params = {'tags': f'{tag1.id}, {tag2.id}'}
        res = self.client.get(BOOKS_URL, params)

        s1 = BookSerializer(book1)
        s2 = BookSerializer(book2)
        s3 = BookSerializer(book3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)


    def test_filter_by_reviews(self):
        """Filter books by reviews Test"""
        book1 = create_book(user=self.user, title='anotherbook4')
        book2 = create_book(user=self.user, title='anotherbook5')
        review1 = Review.objects.create(user=self.user, name='some text1')
        review2 = Review.objects.create(user=self.user, name='some text2')
        book1.reviews.add(review1)
        book2.reviews.add(review2)
        book3 = create_book(user=self.user, title='anotherbook6')

        params = {'reviews': f'{review1.id}, {review2.id}'}
        res = self.client.get(BOOKS_URL, params)

        s1 = BookSerializer(book1)
        s2 = BookSerializer(book2)
        s3 = BookSerializer(book3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)



class ImageUploadTests(TestCase):
    """Tests for the image upload API."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test@example.com',
            'sample123',
        )
        self.client.force_authenticate(self.user)
        self.book = create_book(user=self.user)

    def tearDown(self):
        self.book.image.delete()

    def test_upload_image(self):
        """Test uploading an image to our book."""
        url = image_upload_url(self.book.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.post(url, payload, format='multipart')

        self.book.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.book.image.path))


    def test_upload_image_bad_request(self):
        """Test uploading an invalid image."""
        url = image_upload_url(self.book.id)
        payload = {'image': 'there s no image'}
        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)