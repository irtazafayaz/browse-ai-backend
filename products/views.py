import re

from bson import ObjectId
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .db import products_col, bookmarks_col, edits_col, prompts_col
from .serializers import ProductSerializer, SearchRequestSerializer
from .ai_search import search_products
from .utils import doc_to_product


def _get_bookmarked_ids(user) -> set:
    if user and user.is_authenticated:
        return {b['product_id'] for b in bookmarks_col().find({'user_id': str(user.id)})}
    return set()


# ── List all products ─────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([AllowAny])
def product_list(request):
    """
    GET /api/products/
    Optional: ?q=search+term (simple keyword filter, no AI)
    """
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
@api_view(['GET'])
@permission_classes([AllowAny])
def product_detail(request, product_id):
    """GET /api/products/<product_id>/"""
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
@api_view(['POST'])
@permission_classes([AllowAny])
def product_search(request):
    """POST /api/products/search/"""
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
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_bookmark(request, product_id):
    """POST /api/products/<product_id>/bookmark/"""
    col = bookmarks_col()
    user_id = str(request.user.id)

    existing = col.find_one({'user_id': user_id, 'product_id': product_id})
    if existing:
        col.delete_one({'_id': existing['_id']})
        return Response({'bookmarked': False})

    col.insert_one({'user_id': user_id, 'product_id': product_id})
    return Response({'bookmarked': True}, status=status.HTTP_201_CREATED)


# ── Brands list ───────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([AllowAny])
def brands_list(request):
    """GET /api/products/brands/"""
    return Response(sorted(products_col().distinct('brand')))


# ── Curated edits ─────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([AllowAny])
def edits_list(request):
    """GET /api/products/edits/"""
    docs = list(edits_col().find({}, {'_id': 0}))
    return Response(docs)


# ── Search prompt suggestions ─────────────────────────────────────────
@api_view(['GET'])
@permission_classes([AllowAny])
def prompts_list(request):
    """GET /api/products/prompts/"""
    docs = list(prompts_col().find({}, {'_id': 0, 'text': 1}))
    return Response([d['text'] for d in docs])


# ── User's bookmarks ──────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_bookmarks(request):
    """GET /api/products/bookmarks/"""
    user_id = str(request.user.id)
    bmarks = list(bookmarks_col().find({'user_id': user_id}))
    product_ids = [b['product_id'] for b in bmarks]

    docs = list(products_col().find({'id': {'$in': product_ids}}))
    bookmarked_ids = set(product_ids)
    products = [doc_to_product(d, bookmarked_ids) for d in docs]
    return Response(ProductSerializer(products, many=True).data)
