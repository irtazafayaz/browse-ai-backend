import logging
from datetime import datetime, timezone

from core.db import blog_posts_col

logger = logging.getLogger(__name__)


class BlogPost:
    """
    MongoDB-backed blog post. Not a Django ORM model.
    Stores documents in the 'blog_posts' collection.
    """

    def __init__(self, doc):
        self.id = str(doc['_id'])
        self.slug = doc.get('slug', '')
        self.title = doc.get('title', '')
        self.description = doc.get('description', '')
        self.content = doc.get('content', '')
        self.category = doc.get('category', 'Buying Guide')
        self.read_time = doc.get('read_time', '')
        self.cover_image = doc.get('cover_image', '')
        self.published = doc.get('published', False)
        self.published_at = doc.get('published_at', datetime.now(timezone.utc))
        self.updated_at = doc.get('updated_at', datetime.now(timezone.utc))

    @classmethod
    def list_published(cls):
        cursor = blog_posts_col().find(
            {'published': True},
            sort=[('published_at', -1)],
        )
        return [cls(doc) for doc in cursor]

    @classmethod
    def get_by_slug(cls, slug, published_only=True):
        query = {'slug': slug}
        if published_only:
            query['published'] = True
        doc = blog_posts_col().find_one(query)
        return cls(doc) if doc else None

    @classmethod
    def create(cls, slug, title, **kwargs):
        now = datetime.now(timezone.utc)
        doc = {
            'slug': slug,
            'title': title,
            'description': kwargs.get('description', ''),
            'content': kwargs.get('content', ''),
            'category': kwargs.get('category', 'Buying Guide'),
            'read_time': kwargs.get('read_time', ''),
            'cover_image': kwargs.get('cover_image', ''),
            'published': kwargs.get('published', True),
            'published_at': kwargs.get('published_at', now),
            'updated_at': now,
        }
        result = blog_posts_col().insert_one(doc)
        doc['_id'] = result.inserted_id
        logger.info("BlogPost created: %s", slug)
        return cls(doc)

    @classmethod
    def update_by_slug(cls, slug, **kwargs):
        kwargs['updated_at'] = datetime.now(timezone.utc)
        result = blog_posts_col().update_one({'slug': slug}, {'$set': kwargs})
        if result.matched_count == 0:
            return None
        return cls.get_by_slug(slug, published_only=False)

    @classmethod
    def delete_by_slug(cls, slug):
        result = blog_posts_col().delete_one({'slug': slug})
        return result.deleted_count > 0
