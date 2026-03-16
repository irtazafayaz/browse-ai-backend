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
        posts = BlogPost.objects.filter(published=True)
        return Response(BlogPostListSerializer(posts, many=True).data)

    # POST — staff only
    serializer = BlogPostSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        post = serializer.save()
    except Exception as exc:
        logger.error("Failed to create blog post: %s", exc)
        return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(BlogPostSerializer(post).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsStaffOrReadOnly])
def post_detail(request, slug):
    try:
        post = BlogPost.objects.get(slug=slug, published=True)
    except BlogPost.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(BlogPostSerializer(post).data)

    if request.method == 'PUT':
        serializer = BlogPostSerializer(post, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)

    # DELETE
    post.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
