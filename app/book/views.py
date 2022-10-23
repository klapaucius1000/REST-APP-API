"""
Views for books APIs.
"""

from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Book, Tag, Review
from book import serializers

"""class BaseBookAttrViewSet()"""


class BookViewSet(viewsets.ModelViewSet):
    """View for manage book APIs"""
    serializer_class = serializers.BookDetailSerializer
    queryset = Book.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve books fot auth user."""
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        """Return the serializer class for request."""

        if self.action == 'list':
            return serializers.BookSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new annotation of book."""
        serializer.save(user=self.request.user)


class BaseBookAttrViewSet(mixins.UpdateModelMixin,
                          mixins.DestroyModelMixin,
                          mixins.ListModelMixin,
                          viewsets.GenericViewSet):
    """Base viewsets for books atributes."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter queryset to  auth user."""
        return self.queryset.filter(user=self.request.user).order_by('-name')


class TagViewSet(BaseBookAttrViewSet):
    """Manage tags in the DB"""
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class ReviewViewSet(BaseBookAttrViewSet):
    """Manage reviews in the DB."""
    serializer_class = serializers.ReviewSerializer
    queryset = Review.objects.all()
