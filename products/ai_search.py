import json
import logging

import requests
from django.conf import settings

from .db import bookmarks_col

logger = logging.getLogger('products.ai_search')

AI_SEARCH_URL = getattr(settings, 'AI_SEARCH_URL', 'http://localhost:8001/api/v1/search')
# The AI service exposes three modes under the same base path.
_BASE = AI_SEARCH_URL.rstrip('/')
VISUAL_SEARCH_URL = _BASE + '/visual'   # text -> image (cross-modal)
IMAGE_SEARCH_URL = _BASE + '/image'     # image -> image (upload)
PAGE_SIZE = 24


def _log_response(resp, **_kwargs):
    elapsed_ms = resp.elapsed.total_seconds() * 1000 if resp.elapsed else 0

    try:
        data = resp.json()
        results = data.get('results', [])
        body_repr = json.dumps({
            'results': f'[{len(results)} items]',
            **{k: v for k, v in data.items() if k != 'results'},
        }, ensure_ascii=False)
    except Exception:
        body_repr = resp.text[:300]

    extra = dict(status=resp.status_code, duration_ms=round(elapsed_ms, 1))
    base  = '← AI RESPONSE %s | status=%d | %.1fms | %s'
    args  = (resp.url, resp.status_code, elapsed_ms, body_repr)

    if elapsed_ms > 15_000:
        logger.error(base + ' | ⚠ VERY SLOW', *args, extra=extra)
    elif elapsed_ms > 5_000:
        logger.warning(base + ' | ⚠ SLOW', *args, extra=extra)
    else:
        logger.info(base, *args, extra=extra)


def _build_session() -> requests.Session:
    session = requests.Session()
    session.hooks['response'].append(_log_response)
    return session


def _map_product(item: dict, bookmarked_ids: set) -> dict:
    pid = item.get('productUrl', '')
    return {
        '_id_str':       pid,
        'brand':         item.get('brand', ''),
        'name':          item.get('name', ''),
        'imageUrl':      item.get('imageUrl', ''),
        'price':         float(item.get('price', 0) or 0),
        'originalPrice': None,
        'tags':          item.get('tags', []),
        'category':      item.get('category', ''),
        'productUrl':    item.get('productUrl', ''),
        'score':         item.get('score'),
        'isBookmarked':  pid in bookmarked_ids,
    }


def _bookmarked_ids(user_id) -> set:
    if not user_id:
        return set()
    return {b['product_id'] for b in bookmarks_col().find({'user_id': str(user_id)})}


def _empty_result(display_text: str, page: int, top_k: int) -> dict:
    return {
        'products':         [],
        'displayText':      display_text,
        'suggestedFilters': [],
        'total':            0,
        'page':             page,
        'page_size':        top_k,
        'has_next':         False,
    }


def _build_result(data: dict, display_text: str, page: int, top_k: int, user_id) -> dict:
    """Map an AI-service response ({'results': [...], 'total': N}) into the shape
    the frontend expects. Shared by all three search modes."""
    bookmarked_ids = _bookmarked_ids(user_id)
    products = [_map_product(item, bookmarked_ids) for item in data.get('results', [])]
    total = data.get('total', len(products))
    return {
        'products':         products,
        # .replace (not .format) so literal braces in a user query can't crash formatting.
        'displayText':      display_text.replace('{total}', str(total)),
        'suggestedFilters': [],
        'total':            total,
        'page':             page,
        'page_size':        top_k,
        'has_next':         False,
    }


def search_products(query: str, page: int = 1, user_id=None, top_k: int = PAGE_SIZE, brand: str = '') -> dict:
    """Text search — hybrid semantic + keyword (GET /search)."""
    params = {'q': query, 'top_k': top_k}
    if brand:
        params['brand'] = brand

    logger.info('→ AI REQUEST GET %s | params=%s', AI_SEARCH_URL, json.dumps(params),
                extra=dict(method='GET', path=AI_SEARCH_URL))

    try:
        resp = _build_session().get(AI_SEARCH_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.error('AI text-search error: %s', exc)
        return _empty_result('Search is temporarily unavailable. Please try again.', page, top_k)

    return _build_result(data, f'Found {{total}} results for "{query}"', page, top_k, user_id)


def visual_search_products(query: str, page: int = 1, user_id=None, top_k: int = PAGE_SIZE, brand: str = '') -> dict:
    """Cross-modal text → image search (GET /search/visual)."""
    params = {'q': query, 'top_k': top_k}
    if brand:
        params['brand'] = brand

    logger.info('→ AI REQUEST GET %s | params=%s', VISUAL_SEARCH_URL, json.dumps(params),
                extra=dict(method='GET', path=VISUAL_SEARCH_URL))

    try:
        resp = _build_session().get(VISUAL_SEARCH_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.error('AI visual-search error: %s', exc)
        return _empty_result('Visual search is temporarily unavailable. Please try again.', page, top_k)

    return _build_result(data, f'Found {{total}} results for "{query}"', page, top_k, user_id)


def image_search_products(
    image_bytes: bytes,
    filename: str = 'upload.jpg',
    content_type: str = 'image/jpeg',
    page: int = 1,
    user_id=None,
    top_k: int = PAGE_SIZE,
    brand: str = '',
) -> dict:
    """Image → image search — forward the uploaded photo to POST /search/image."""
    params = {'top_k': top_k}
    if brand:
        params['brand'] = brand
    files = {'file': (filename, image_bytes, content_type or 'image/jpeg')}

    logger.info('→ AI REQUEST POST %s | file=%s (%d bytes)', IMAGE_SEARCH_URL, filename, len(image_bytes or b''),
                extra=dict(method='POST', path=IMAGE_SEARCH_URL))

    try:
        # Longer timeout: server downloads/encodes the image with CLIP.
        resp = _build_session().post(IMAGE_SEARCH_URL, params=params, files=files, timeout=60)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.error('AI image-search error: %s', exc)
        return _empty_result('Image search is temporarily unavailable. Please try again.', page, top_k)

    return _build_result(data, 'Found {total} visually similar products', page, top_k, user_id)
