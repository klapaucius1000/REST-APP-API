"""
Serializers for book APIs.
"""

from rest_framework import serializers

from core.models import Book, Tag, Review


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for reviews"""

    class Meta:
        model = Review
        fields = ['id', 'name']
        read_only_fields = ['id']


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags"""

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class BookSerializer(serializers.ModelSerializer):
    """Serializer for books"""
    tags = TagSerializer(many=True, required=False)
    reviews = ReviewSerializer(many=True, required=False)

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'number_of_pages', 'category',
            'language', 'link', 'tags', 'reviews',
        ]
        read_only_fields = ['id']

    def _get_or_create_tags(self, tags, book):
        """Handle getting or creating tags as needed."""
        auth_user = self.context['request'].user
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user=auth_user,
                **tag,
            )
            book.tags.add(tag_obj)

    def _get_or_create_reviews(self, reviews, book):
        """Handle getting or creating reviews as needed."""
        auth_user = self.context['request'].user
        for review in reviews:
            review_obj, create = Review.objects.get_or_create(
                user=auth_user,
                **review,
            )
            book.reviews.add(review_obj)

    def create(self, validated_data):
        """Create a book."""
        tags = validated_data.pop('tags', [])
        reviews = validated_data.pop('reviews', [])
        book = Book.objects.create(**validated_data)
        self._get_or_create_tags(tags, book)
        self._get_or_create_reviews(reviews, book)

        return book

    def update(self, instance, validated_data):
        """Update book."""
        tags = validated_data.pop('tags', None)
        reviews = validated_data.pop('reviews', None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)
        if reviews is not None:
            instance.reviews.clear()
            self._get_or_create_reviews(reviews, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class BookDetailSerializer(BookSerializer):
    """Serializer for book details view"""

    class Meta(BookSerializer.Meta):
        fields = BookSerializer.Meta.fields + ['description']


class BookImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading images to books."""

    class Meta:
        model = Book
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs = {'image': {'required': 'True'}}