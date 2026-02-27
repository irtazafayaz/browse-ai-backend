from bson import ObjectId
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .db import products_col, bookmarks_col, get_db
from .serializers import ProductSerializer, SearchRequestSerializer
from .ai_search import search_products


def _doc_to_product(doc, bookmarked_ids=None):
    """Convert a MongoDB document to the frontend Product shape."""
    bookmarked_ids = bookmarked_ids or set()
    pid = doc.get('id', str(doc['_id']))
    return {
        '_id_str': pid,
        'brand': doc.get('brand', ''),
        'name': doc.get('name', ''),
        'imageUrl': doc.get('imageUrl', ''),
        'price': doc.get('price', 0),
        'originalPrice': doc.get('originalPrice'),
        'tags': doc.get('tags', []),
        'isBookmarked': pid in bookmarked_ids,
    }


def _get_bookmarked_ids(user):
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
    Returns list of products.
    """
    q = request.query_params.get('q', '').strip()
    col = products_col()

    if q:
        import re
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
    products = [_doc_to_product(d, bookmarked_ids) for d in docs]
    return Response(ProductSerializer(products, many=True).data)


# ── Single product ────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([AllowAny])
def product_detail(request, product_id):
    """
    GET /api/products/<product_id>/
    Returns a single product by its string id (e.g. 'p001').
    """
    col = products_col()
    doc = col.find_one({'id': product_id})

    if not doc:
        # Try by MongoDB ObjectId
        try:
            doc = col.find_one({'_id': ObjectId(product_id)})
        except Exception:
            pass

    if not doc:
        return Response({'detail': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

    bookmarked_ids = _get_bookmarked_ids(request.user)
    return Response(ProductSerializer(_doc_to_product(doc, bookmarked_ids)).data)


# ── AI search ─────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def product_search(request):
    """
    POST /api/products/search/
    Body: { query: string, history?: ChatMessage[] }
    Returns: { products, displayText, suggestedFilters }
    """
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
    """
    POST /api/products/<product_id>/bookmark/
    Toggles the bookmark for the authenticated user.
    Returns: { bookmarked: bool }
    """
    col = bookmarks_col()
    user_id = str(request.user.id)

    existing = col.find_one({'user_id': user_id, 'product_id': product_id})
    if existing:
        col.delete_one({'_id': existing['_id']})
        return Response({'bookmarked': False})
    else:
        col.insert_one({'user_id': user_id, 'product_id': product_id})
        return Response({'bookmarked': True}, status=status.HTTP_201_CREATED)


# ── Brands list ──────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([AllowAny])
def brands_list(request):
    """GET /api/products/brands/ — distinct brand names from the products collection."""
    col = products_col()
    brands = col.distinct('brand')
    return Response(sorted(brands))


# ── Curated edits ─────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([AllowAny])
def edits_list(request):
    """GET /api/products/edits/ — curated editorial collections."""
    col = get_db()['edits']
    docs = list(col.find({}, {'_id': 0}))
    return Response(docs)


# ── Search prompt suggestions ─────────────────────────────────────────
@api_view(['GET'])
@permission_classes([AllowAny])
def prompts_list(request):
    """GET /api/products/prompts/ — rotating search placeholder prompts."""
    col = get_db()['prompts']
    docs = list(col.find({}, {'_id': 0, 'text': 1}))
    return Response([d['text'] for d in docs])


# ── User's bookmarks ──────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_bookmarks(request):
    """
    GET /api/products/bookmarks/
    Returns all products bookmarked by the authenticated user.
    """
    user_id = str(request.user.id)
    bmarks = list(bookmarks_col().find({'user_id': user_id}))
    product_ids = [b['product_id'] for b in bmarks]

    col = products_col()
    docs = list(col.find({'id': {'$in': product_ids}}))
    bookmarked_ids = set(product_ids)
    products = [_doc_to_product(d, bookmarked_ids) for d in docs]
    return Response(ProductSerializer(products, many=True).data)
