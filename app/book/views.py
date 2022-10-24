"""
Views for books APIs.
"""

from rest_framework import viewsets, mixins, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

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
        elif self.action == 'upload_image':
            return serializers.BookImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new annotation of book."""
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Upload an image to the book."""
        book = self.get_object()
        serializer = self.get_serializer(book, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
