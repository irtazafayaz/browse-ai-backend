from django.db import models
from django.utils import timezone


class BlogPost(models.Model):
    slug = models.SlugField(unique=True, max_length=200)
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    content = models.TextField(blank=True)
    category = models.CharField(max_length=100, default='Buying Guide')
    read_time = models.CharField(max_length=50, default='5 min read')
    cover_image = models.URLField(blank=True)
    published = models.BooleanField(default=True)
    published_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_at']

    def __str__(self):
        return self.title
