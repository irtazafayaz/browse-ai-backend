import json
import logging

import requests
from django.conf import settings

from .db import bookmarks_col

logger = logging.getLogger('products.ai_search')

BROWSEBY_API_URL = 'https://browsebyai-production.up.railway.app/api/v1/search/text'


def _log_response(resp, **_kwargs):
    elapsed_ms = resp.elapsed.total_seconds() * 1000 if resp.elapsed else 0

    try:
        data = resp.json()
        results = data.get('results', data.get('products', []))
        body_repr = json.dumps({
            'results': f'[{len(results)} items]',
            **{k: v for k, v in data.items() if k not in ('results', 'products')},
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
    pid = str(item.get('id', item.get('mongo_id', '')))
    return {
        '_id_str':       pid,
        'brand':         item.get('store_name', ''),
        'name':          item.get('title', ''),
        'imageUrl':      item.get('featured_image', ''),
        'price':         float(item.get('price_min', 0) or 0),
        'originalPrice': float(item.get('price_max', 0) or 0) or None,
        'tags':          item.get('tags', []),
        'isBookmarked':  pid in bookmarked_ids,
    }


def search_products(query: str, page: int = 1, user_id=None) -> dict:
    api_key = getattr(settings, 'BROWSEBY_API_KEY', '')
    payload = {'query': query, 'page': page}

    logger.info(
        '→ AI REQUEST POST %s | body=%s',
        BROWSEBY_API_URL,
        json.dumps(payload),
        extra=dict(method='POST', path=BROWSEBY_API_URL),
    )

    try:
        resp = _build_session().post(
            BROWSEBY_API_URL,
            headers={'X-API-Key': api_key},
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

    except requests.RequestException as exc:
        logger.error('AI API error: %s', exc)
        return {
            'products':       [],
            'displayText':    'Search is temporarily unavailable. Please try again.',
            'suggestedFilters': [],
            'total':          0,
            'page':           page,
            'page_size':      24,
            'has_next':       False,
        }

    bookmarked_ids: set = set()
    if user_id:
        bookmarked_ids = {
            b['product_id'] for b in bookmarks_col().find({'user_id': str(user_id)})
        }

    raw_products = data.get('results', [])
    products     = [_map_product(item, bookmarked_ids) for item in raw_products]

    pagination  = data.get('pagination', {})
    page_size   = pagination.get('page_size', 10)
    total       = pagination.get('total_results', len(products))
    total_pages = pagination.get('total_pages', 1)

    return {
        'products':         products,
        'displayText':      f'Found {total} results for "{query}"',
        'suggestedFilters': [],
        'total':            total,
        'page':             page,
        'page_size':        page_size,
        'has_next':         page < total_pages,
    }
