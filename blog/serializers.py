from rest_framework import serializers
from .models import BlogPost


class BlogPostSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)

    class Meta:
        model = BlogPost
        fields = [
            'id', 'slug', 'title', 'description', 'content',
            'category', 'read_time', 'cover_image',
            'published', 'published_at', 'updated_at',
        ]
        read_only_fields = ['id', 'updated_at']


class BlogPostListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list responses — omits content."""
    id = serializers.CharField(read_only=True)

    class Meta:
        model = BlogPost
        fields = [
            'id', 'slug', 'title', 'description',
            'category', 'read_time', 'cover_image', 'published_at',
        ]
        read_only_fields = ['id']
