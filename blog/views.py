import logging

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status

from .models import BlogPost
from .serializers import BlogPostSerializer, BlogPostListSerializer
from .permissions import IsStaffOrReadOnly

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
@permission_classes([IsStaffOrReadOnly])
def post_list(request):
    if request.method == 'GET':
        posts = BlogPost.list_published()
        return Response(BlogPostListSerializer(posts, many=True).data)

    # POST — staff only
    serializer = BlogPostSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        post = BlogPost.create(**serializer.validated_data)
    except Exception as exc:
        logger.error("Failed to create blog post: %s", exc)
        return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(BlogPostSerializer(post).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsStaffOrReadOnly])
def post_detail(request, slug):
    if request.method == 'GET':
        post = BlogPost.get_by_slug(slug)
        if not post:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(BlogPostSerializer(post).data)

    if request.method == 'PUT':
        serializer = BlogPostSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        post = BlogPost.update_by_slug(slug, **serializer.validated_data)
        if not post:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(BlogPostSerializer(post).data)

    # DELETE
    deleted = BlogPost.delete_by_slug(slug)
    if not deleted:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    return Response(status=status.HTTP_204_NO_CONTENT)
