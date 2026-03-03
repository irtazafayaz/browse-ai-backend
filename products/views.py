import re

from bson import ObjectId
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
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


def _get_bookmarked_ids(user) -> set:
    if user and user.is_authenticated:
        return {b['product_id'] for b in bookmarks_col().find({'user_id': str(user.id)})}
    return set()


# ── List all products ─────────────────────────────────────────────────
@extend_schema(
    tags=['Products'],
    summary='List products',
    description=(
        'Returns all products. Optionally filter by keyword using `?q=`.\n\n'
        'The `q` parameter performs a simple regex match against product tags — '
        'no AI is involved. For AI-powered search use `POST /api/products/search/`.'
    ),
    parameters=[
        OpenApiParameter(
            name='q',
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
            description='Keyword filter. Matches against product tags (case-insensitive).',
            examples=[
                OpenApiExample('Jeans', value='jeans'),
                OpenApiExample('Blue slim', value='blue slim'),
            ],
        )
    ],
    responses={
        200: OpenApiResponse(
            response=ProductSerializer(many=True),
            description='List of products.',
            examples=[
                OpenApiExample('Product list', value=[_PRODUCT_EXAMPLE])
            ],
        )
    },
)
@api_view(['GET'])
@permission_classes([AllowAny])
def product_list(request):
    q = request.query_params.get('q', '').strip()
    col = products_col()

    if q:
        words = [w for w in re.split(r'\s+', q.lower()) if w]
        mongo_filter = {
            'tags': {
                '$elemMatch': {
                    '$regex': '|'.join(re.escape(w) for w in words),
                    '$options': 'i',
                }
            }
        }
        docs = list(col.find(mongo_filter))
    else:
        docs = list(col.find())

    bookmarked_ids = _get_bookmarked_ids(request.user)
    products = [doc_to_product(d, bookmarked_ids) for d in docs]
    return Response(ProductSerializer(products, many=True).data)


# ── Single product ────────────────────────────────────────────────────
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
        'Search products using natural language. Claude AI extracts filter tags '
        'from your query and returns matching products with a human-readable display text '
        'and suggested follow-up filters.\n\n'
        'Optionally pass conversation `history` (array of `{role, content}` objects) '
        'to make the search context-aware across turns.'
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
                    },
                )
            ],
        ),
        400: OpenApiResponse(description='Validation error (e.g. missing query).'),
    },
    examples=[
        OpenApiExample(
            'Simple search',
            value={'query': 'slim fit blue jeans under 100 dollars', 'history': []},
            request_only=True,
        ),
        OpenApiExample(
            'Search with history',
            value={
                'query': 'show me something darker',
                'history': [
                    {'role': 'user', 'content': 'slim fit blue jeans'},
                    {'role': 'assistant', 'content': 'Here are some slim-fit blue jeans.'},
                ],
            },
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
    history = serializer.validated_data['history']
    user_id = request.user.id if request.user.is_authenticated else None

    result = search_products(query, history, user_id)
    return Response({
        'products': ProductSerializer(result['products'], many=True).data,
        'displayText': result['displayText'],
        'suggestedFilters': result['suggestedFilters'],
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
                        'What are the most popular jeans right now?',
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
