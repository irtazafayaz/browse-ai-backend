import json
import logging

import requests
from django.conf import settings

from .db import bookmarks_col

logger = logging.getLogger('products.ai_search')

AI_SEARCH_URL = getattr(settings, 'AI_SEARCH_URL', 'http://localhost:8001/api/v1/search')
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


def search_products(query: str, page: int = 1, user_id=None, top_k: int = PAGE_SIZE, brand: str = '') -> dict:
    params = {'q': query, 'top_k': top_k}
    if brand:
        params['brand'] = brand

    logger.info(
        '→ AI REQUEST GET %s | params=%s',
        AI_SEARCH_URL,
        json.dumps(params),
        extra=dict(method='GET', path=AI_SEARCH_URL),
    )

    try:
        resp = _build_session().get(AI_SEARCH_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

    except requests.RequestException as exc:
        logger.error('AI API error: %s', exc)
        return {
            'products':         [],
            'displayText':      'Search is temporarily unavailable. Please try again.',
            'suggestedFilters': [],
            'total':            0,
            'page':             page,
            'page_size':        PAGE_SIZE,
            'has_next':         False,
        }

    bookmarked_ids: set = set()
    if user_id:
        bookmarked_ids = {
            b['product_id'] for b in bookmarks_col().find({'user_id': str(user_id)})
        }

    raw_products = data.get('results', [])
    products     = [_map_product(item, bookmarked_ids) for item in raw_products]
    total        = data.get('total', len(products))

    return {
        'products':         products,
        'displayText':      f'Found {total} results for "{query}"',
        'suggestedFilters': [],
        'total':            total,
        'page':             page,
        'page_size':        top_k,
        'has_next':         False,
    }
