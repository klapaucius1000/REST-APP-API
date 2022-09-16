"""
Serializers for book APIs.
"""

from rest_framework import serializers

from core.models import Book


class BookSerializer(serializers.ModelSerializer):
	"""Serializer for books"""

	class Meta:
		model = Book
		fields = ['id', 'title', 'author', 'number_of_pages', 'category', 'language', 'link']
		read_only_fields = ['id']


class BookDetailSerializer(BookSerializer):
	"""Serializer for book details view"""

	class Meta(BookSerializer.Meta):
		fields = BookSerializer.Meta.fields + ['description']