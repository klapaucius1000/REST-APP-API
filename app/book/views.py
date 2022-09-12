"""
Views for books APIs.
"""

from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Book
from book import serializers


class BookViewSet(viewsets.ModelViewSet):
	"""View for manage book APIs"""
	serializer_class = serializers.BookSerializer
	queryset = Book.objects.all()
	authentication_classes = [TokenAuthentication]
	permission_classes = [IsAuthenticated]

	def get_queryset(self):
		"""Retrieve books fot auth user."""
		return self.queryset.filter(user=self.request.user).order_by('-id')
