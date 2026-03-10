import re

from bson import ObjectId
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import (
    extend_schema, OpenApiExample, OpenApiResponse,
    OpenApiParameter, inline_serializer,
)
from rest_framework import serializers as drf_serializers

from .db import products_col, bookmarks_col, edits_col, prompts_col
from .serializers import ProductSerializer, SearchRequestSerializer, SearchResponseSerializer
from .ai_search import search_products
from .utils import doc_to_product


_PRODUCT_EXAMPLE = {
    'id': 'prod_001',
    'brand': 'Levi\'s',
    'name': '501 Original Fit Jeans',
    'imageUrl': 'https://example.com/images/levis-501.jpg',
    'price': 79.99,
    'originalPrice': 99.99,
    'tags': ['jeans', 'denim', 'classic', 'straight', 'blue'],
    'isBookmarked': False,
}

_PAGINATED_EXAMPLE = {
    'products': [_PRODUCT_EXAMPLE],
    'total': 150,
    'page': 1,
    'page_size': 24,
    'has_next': True,
}


def _get_bookmarked_ids(user) -> set:
    if user and user.is_authenticated:
        return {b['product_id'] for b in bookmarks_col().find({'user_id': str(user.id)})}
    return set()


def _paginated_response(col, mongo_filter, page, page_size, bookmarked_ids):
    """Run a paginated MongoDB query and return a standard response dict."""
    total = col.count_documents(mongo_filter)
    skip = (page - 1) * page_size
    docs = list(col.find(mongo_filter).skip(skip).limit(page_size))
    products = [doc_to_product(d, bookmarked_ids) for d in docs]
    return {
        'products': ProductSerializer(products, many=True).data,
        'total': total,
        'page': page,
        'page_size': page_size,
        'has_next': (skip + len(docs)) < total,
    }


# ── List / search products ─────────────────────────────────────────────
@extend_schema(
    tags=['Products'],
    summary='List products',
    description=(
        'Returns a paginated list of products. Supports keyword search (`?q=`) '
        'and filters for brand, price range, and tags.\n\n'
        '`q` performs a regex match across product name, brand, and tags. '
        'For AI-powered search use `POST /api/products/search/`.'
    ),
    parameters=[
        OpenApiParameter('q', str, OpenApiParameter.QUERY, required=False,
                         description='Keyword search across name, brand, and tags.'),
        OpenApiParameter('page', int, OpenApiParameter.QUERY, required=False,
                         description='Page number (default: 1).'),
        OpenApiParameter('page_size', int, OpenApiParameter.QUERY, required=False,
                         description='Results per page (default: 24, max: 100).'),
        OpenApiParameter('brand', str, OpenApiParameter.QUERY, required=False,
                         description='Filter by brand name (exact, case-insensitive).'),
        OpenApiParameter('min_price', float, OpenApiParameter.QUERY, required=False,
                         description='Minimum price filter.'),
        OpenApiParameter('max_price', float, OpenApiParameter.QUERY, required=False,
                         description='Maximum price filter.'),
        OpenApiParameter('tags', str, OpenApiParameter.QUERY, required=False,
                         description='Comma-separated list of tags to filter by (e.g. `slim,blue`).'),
    ],
    responses={
        200: OpenApiResponse(
            description='Paginated product list.',
            examples=[OpenApiExample('Paginated products', value=_PAGINATED_EXAMPLE)],
        )
    },
)
@api_view(['GET'])
@permission_classes([AllowAny])
def product_list(request):
    # ── Parse params ──
    q = request.query_params.get('q', '').strip()
    brand = request.query_params.get('brand', '').strip()
    tags_param = request.query_params.get('tags', '').strip()
    min_price_str = request.query_params.get('min_price', '').strip()
    max_price_str = request.query_params.get('max_price', '').strip()

    try:
        page = max(1, int(request.query_params.get('page', 1)))
    except (ValueError, TypeError):
        page = 1

    try:
        page_size = min(100, max(1, int(request.query_params.get('page_size', 24))))
    except (ValueError, TypeError):
        page_size = 24

    # ── Build MongoDB filter ──
    mongo_filter = {}

    # Full-text search across name, brand, tags
    if q:
        words = [w for w in re.split(r'\s+', q.lower()) if w]
        regex_pattern = '|'.join(re.escape(w) for w in words)
        mongo_filter['$or'] = [
            {'tags': {'$elemMatch': {'$regex': regex_pattern, '$options': 'i'}}},
            {'name': {'$regex': regex_pattern, '$options': 'i'}},
            {'brand': {'$regex': regex_pattern, '$options': 'i'}},
        ]

    # Brand filter (exact, case-insensitive)
    if brand:
        mongo_filter['brand'] = {'$regex': f'^{re.escape(brand)}$', '$options': 'i'}

    # Tags filter (comma-separated, case-insensitive exact match)
    if tags_param:
        tag_list = [t.strip().lower() for t in tags_param.split(',') if t.strip()]
        if tag_list:
            mongo_filter['tags'] = {'$in': tag_list}

    # Price range filter
    price_filter = {}
    if min_price_str:
        try:
            price_filter['$gte'] = float(min_price_str)
        except ValueError:
            pass
    if max_price_str:
        try:
            price_filter['$lte'] = float(max_price_str)
        except ValueError:
            pass
    if price_filter:
        mongo_filter['price'] = price_filter

    col = products_col()
    bookmarked_ids = _get_bookmarked_ids(request.user)
    return Response(_paginated_response(col, mongo_filter, page, page_size, bookmarked_ids))


# ── Image search (stub) ────────────────────────────────────────────────
@extend_schema(
    tags=['Products'],
    summary='Image-based product search (stub)',
    description=(
        'Upload a product image to find visually similar products.\n\n'
        '**Note:** This endpoint is currently a stub. It returns a paginated list of '
        'all products from MongoDB. The AI vision service integration will replace this '
        'logic once available. The request/response shape will remain the same.\n\n'
        'Send as `multipart/form-data` with an `image` file field.'
    ),
    request=inline_serializer(
        name='ImageSearchRequest',
        fields={
            'image': drf_serializers.ImageField(),
            'page': drf_serializers.IntegerField(required=False, default=1),
        },
    ),
    responses={
        200: OpenApiResponse(
            description='Paginated products (stub: returns all products).',
            examples=[OpenApiExample('Image search result', value=_PAGINATED_EXAMPLE)],
        )
    },
)
@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
def image_search(request):
    """
    Stub: returns all products paginated.
    TODO: Replace with AI vision service call once available.
    The service will receive the uploaded image bytes and return semantically
    similar product IDs which are then fetched from MongoDB.
    """
    try:
        page = max(1, int(request.data.get('page', 1)))
    except (ValueError, TypeError):
        page = 1

    page_size = 24
    col = products_col()
    bookmarked_ids = _get_bookmarked_ids(request.user)
    return Response(_paginated_response(col, {}, page, page_size, bookmarked_ids))


# ── Single product ─────────────────────────────────────────────────────
@extend_schema(
    tags=['Products'],
    operation_id='products_detail',
    summary='Get product by ID',
    description='Fetch a single product by its `id` field or MongoDB `_id`.',
    responses={
        200: OpenApiResponse(
            response=ProductSerializer,
            description='Product found.',
            examples=[OpenApiExample('Product', value=_PRODUCT_EXAMPLE)],
        ),
        404: OpenApiResponse(description='Product not found.'),
    },
)
@api_view(['GET'])
@permission_classes([AllowAny])
def product_detail(request, product_id):
    col = products_col()
    doc = col.find_one({'id': product_id})

    if not doc:
        try:
            doc = col.find_one({'_id': ObjectId(product_id)})
        except Exception:
            pass

    if not doc:
        return Response({'detail': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

    bookmarked_ids = _get_bookmarked_ids(request.user)
    return Response(ProductSerializer(doc_to_product(doc, bookmarked_ids)).data)


# ── AI search ─────────────────────────────────────────────────────────
@extend_schema(
    tags=['Products'],
    summary='AI-powered product search',
    description=(
        'Search products using natural language via the BrowseBy AI API. '
        'Returns matching products with a human-readable display text, '
        'suggested follow-up filters, and pagination metadata.\n\n'
        'Pass `page` (default: 1) to paginate through results.'
    ),
    request=SearchRequestSerializer,
    responses={
        200: OpenApiResponse(
            response=SearchResponseSerializer,
            description='Search results.',
            examples=[
                OpenApiExample(
                    'Search result',
                    value={
                        'products': [_PRODUCT_EXAMPLE],
                        'displayText': 'Here are some slim-fit blue jeans under $100.',
                        'suggestedFilters': ['skinny', 'stretch', 'dark wash'],
                        'total': 48,
                        'page': 1,
                        'page_size': 24,
                        'has_next': True,
                    },
                )
            ],
        ),
        400: OpenApiResponse(description='Validation error (e.g. missing query).'),
    },
    examples=[
        OpenApiExample(
            'Simple search',
            value={'query': 'slim fit blue jeans under 100 dollars', 'page': 1},
            request_only=True,
        ),
    ],
)
@api_view(['POST'])
@permission_classes([AllowAny])
def product_search(request):
    serializer = SearchRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    query = serializer.validated_data['query']
    page = serializer.validated_data['page']
    user_id = request.user.id if request.user.is_authenticated else None

    result = search_products(query, page, user_id)
    return Response({
        'products': ProductSerializer(result['products'], many=True).data,
        'displayText': result['displayText'],
        'suggestedFilters': result['suggestedFilters'],
        'total': result['total'],
        'page': result['page'],
        'page_size': result['page_size'],
        'has_next': result['has_next'],
    })


# ── Toggle bookmark ───────────────────────────────────────────────────
@extend_schema(
    tags=['Bookmarks'],
    summary='Toggle bookmark',
    request=None,
    description=(
        'Add or remove a bookmark for the given product.\n\n'
        '- If the product is **not bookmarked**, it will be added → returns `{"bookmarked": true}` (HTTP 201).\n'
        '- If the product **is already bookmarked**, it will be removed → returns `{"bookmarked": false}` (HTTP 200).\n\n'
        '**Requires authentication.**'
    ),
    responses={
        200: OpenApiResponse(
            response=inline_serializer(
                name='BookmarkRemovedResponse',
                fields={'bookmarked': drf_serializers.BooleanField()},
            ),
            description='Bookmark removed.',
            examples=[OpenApiExample('Removed', value={'bookmarked': False})],
        ),
        201: OpenApiResponse(
            response=inline_serializer(
                name='BookmarkAddedResponse',
                fields={'bookmarked': drf_serializers.BooleanField()},
            ),
            description='Bookmark added.',
            examples=[OpenApiExample('Added', value={'bookmarked': True})],
        ),
        401: OpenApiResponse(description='Authentication required.'),
    },
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_bookmark(request, product_id):
    col = bookmarks_col()
    user_id = str(request.user.id)

    existing = col.find_one({'user_id': user_id, 'product_id': product_id})
    if existing:
        col.delete_one({'_id': existing['_id']})
        return Response({'bookmarked': False})

    col.insert_one({'user_id': user_id, 'product_id': product_id})
    return Response({'bookmarked': True}, status=status.HTTP_201_CREATED)


# ── Brands list ───────────────────────────────────────────────────────
@extend_schema(
    tags=['Collections'],
    summary='List brands',
    description='Returns a sorted list of all distinct brand names in the product catalog.',
    responses={
        200: OpenApiResponse(
            response=inline_serializer(
                name='BrandsResponse',
                fields={'brands': drf_serializers.ListField(
                    child=drf_serializers.CharField())},
            ),
            description='Sorted brand names.',
            examples=[
                OpenApiExample(
                    'Brands',
                    value=["AG Jeans", "Frame", "Levi's",
                           "Madewell", "Paige", "Wrangler"],
                )
            ],
        )
    },
)
@api_view(['GET'])
@permission_classes([AllowAny])
def brands_list(request):
    return Response(sorted(products_col().distinct('brand')))


# ── Curated edits ─────────────────────────────────────────────────────
@extend_schema(
    tags=['Collections'],
    summary='List curated editorial collections',
    description=(
        'Returns editorial product collections (e.g. "Summer Essentials", "Classic Denim").\n\n'
        'Each edit has a `label`, `imageUrl`, and `tag` that can be used as a search filter.'
    ),
    responses={
        200: OpenApiResponse(
            response=inline_serializer(
                name='EditItem',
                fields={
                    'label': drf_serializers.CharField(),
                    'imageUrl': drf_serializers.CharField(),
                    'tag': drf_serializers.CharField(),
                },
            ),
            description='List of editorial collections.',
            examples=[
                OpenApiExample(
                    'Edits',
                    value=[
                        {'label': 'Classic Denim',
                            'imageUrl': 'https://example.com/classic.jpg', 'tag': 'classic'},
                        {'label': 'Slim & Sleek',
                            'imageUrl': 'https://example.com/slim.jpg', 'tag': 'slim'},
                    ],
                )
            ],
        )
    },
)
@api_view(['GET'])
@permission_classes([AllowAny])
def edits_list(request):
    docs = list(edits_col().find({}, {'_id': 0}))
    return Response(docs)


# ── Search prompt suggestions ─────────────────────────────────────────
@extend_schema(
    tags=['Collections'],
    summary='List search prompt suggestions',
    description='Returns pre-written search prompt suggestions to inspire users.',
    responses={
        200: OpenApiResponse(
            response=inline_serializer(
                name='PromptsResponse',
                fields={'prompts': drf_serializers.ListField(
                    child=drf_serializers.CharField())},
            ),
            description='List of prompt strings.',
            examples=[
                OpenApiExample(
                    'Prompts',
                    value=[
                        'Show me slim fit jeans under $100',
                        'Find dark wash straight leg denim',
                    ],
                )
            ],
        )
    },
)
@api_view(['GET'])
@permission_classes([AllowAny])
def prompts_list(request):
    docs = list(prompts_col().find({}, {'_id': 0, 'text': 1}))
    return Response([d['text'] for d in docs])


# ── User's bookmarks ──────────────────────────────────────────────────
@extend_schema(
    tags=['Bookmarks'],
    summary='List my bookmarks',
    description='Returns all products bookmarked by the authenticated user.',
    responses={
        200: OpenApiResponse(
            response=ProductSerializer(many=True),
            description='Bookmarked products.',
            examples=[
                OpenApiExample(
                    'Bookmarks',
                    value=[{**_PRODUCT_EXAMPLE, 'isBookmarked': True}],
                )
            ],
        ),
        401: OpenApiResponse(description='Authentication required.'),
    },
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_bookmarks(request):
    user_id = str(request.user.id)
    bmarks = list(bookmarks_col().find({'user_id': user_id}))
    product_ids = [b['product_id'] for b in bmarks]

    docs = list(products_col().find({'id': {'$in': product_ids}}))
    bookmarked_ids = set(product_ids)
    products = [doc_to_product(d, bookmarked_ids) for d in docs]
    return Response(ProductSerializer(products, many=True).data)
