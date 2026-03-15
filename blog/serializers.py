from rest_framework import serializers


class BlogPostSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    slug = serializers.SlugField(max_length=200)
    title = serializers.CharField(max_length=300)
    description = serializers.CharField(max_length=600, required=False, default='')
    content = serializers.CharField(required=False, default='')
    category = serializers.CharField(max_length=100, required=False, default='Buying Guide')
    read_time = serializers.CharField(max_length=50, required=False, default='5 min read')
    cover_image = serializers.URLField(allow_blank=True, required=False, default='')
    published = serializers.BooleanField(required=False, default=True)
    published_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class BlogPostListSerializer(serializers.Serializer):
    """Lightweight serializer for list responses — omits content."""
    id = serializers.CharField(read_only=True)
    slug = serializers.SlugField()
    title = serializers.CharField()
    description = serializers.CharField()
    category = serializers.CharField()
    read_time = serializers.CharField()
    cover_image = serializers.URLField(allow_blank=True)
    published_at = serializers.DateTimeField()
