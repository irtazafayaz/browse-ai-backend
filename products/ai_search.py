"""
AI-powered text search via the BrowseBy AI external API.

Products are fetched entirely from the external AI API — no MongoDB queries.
On any failure the response contains an empty product list; there is no
database fallback and no mock data.

Outgoing requests are intercepted and logged by a requests.Session hook
to the 'products.ai_search' logger (wired in settings.LOGGING).
"""
import json
import logging

import requests
from django.conf import settings

from .db import bookmarks_col

logger = logging.getLogger('products.ai_search')

BROWSEBY_API_URL = 'https://browsebyai-production.up.railway.app/api/v1/search/text'


# ── Outgoing request interceptor ─────────────────────────────────────────────

def _log_response(resp, **_kwargs):
    """
    requests response hook — called automatically after every response.
    Logs status, URL, timing, and a short body summary.
    """
    elapsed_ms = resp.elapsed.total_seconds() * 1000 if resp.elapsed else 0
    try:
        data = resp.json()
        count = len(data.get('results', data.get('products', [])))
        pagination = data.get('pagination', {})
        total = pagination.get('total_results', count)
        body_repr = f'{{results: [{count} items], total: {total}, ...}}'
    except Exception:
        body_repr = resp.text[:200]

    logger.info(
        '← AI RESPONSE %s | status=%d | %.1fms | body=%s',
        resp.url,
        resp.status_code,
        elapsed_ms,
        body_repr,
    )


def _build_session() -> requests.Session:
    """Return a Session with the response-logging hook attached."""
    session = requests.Session()
    session.hooks['response'].append(_log_response)
    return session


# ── Product field mapping ────────────────────────────────────────────────────
# BrowseBy API response shape per result item:
#   id, mongo_id, store_name, title, product_type,
#   price_min, price_max, currency,
#   featured_image, product_url, tags, available, score, match_source

def _map_product(item: dict, bookmarked_ids: set) -> dict:
    pid = str(item.get('id', item.get('mongo_id', '')))
    return {
        '_id_str': pid,
        'brand': item.get('store_name', ''),
        'name': item.get('title', ''),
        'imageUrl': item.get('featured_image', ''),
        'price': float(item.get('price_min', 0) or 0),
        'originalPrice': float(item.get('price_max', 0) or 0) or None,
        'tags': item.get('tags', []),
        'isBookmarked': pid in bookmarked_ids,
    }


# ── Public entry point ───────────────────────────────────────────────────────

def search_products(query: str, page: int = 1, user_id=None) -> dict:
    """
    Call the BrowseBy AI text-search API and return a standardised result dict:
    { products, displayText, suggestedFilters, total, page, page_size, has_next }

    On any network or API error → returns an empty product list with no DB fallback.
    """
    api_key = getattr(settings, 'BROWSEBY_API_KEY', '')

    payload = {'query': query, 'page': page}
    logger.info(
        '→ AI REQUEST  POST %s | body=%s',
        BROWSEBY_API_URL,
        json.dumps(payload),
    )

    session = _build_session()

    try:
        resp = session.post(
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
            'products': [],
            'displayText': 'Search is temporarily unavailable. Please try again.',
            'suggestedFilters': [],
            'total': 0,
            'page': page,
            'page_size': 24,
            'has_next': False,
        }

    # ── Resolve bookmarked IDs for authenticated users ──────────────────
    bookmarked_ids: set = set()
    if user_id:
        bookmarked_ids = {
            b['product_id'] for b in bookmarks_col().find({'user_id': str(user_id)})
        }

    # ── Map API response → our product shape ────────────────────────────
    # Response shape: { query, results: [...], pagination: { page, page_size,
    #                   total_results, total_pages }, sources: {...} }
    raw_products = data.get('results', [])
    products = [_map_product(item, bookmarked_ids) for item in raw_products]

    pagination = data.get('pagination', {})
    page_size = pagination.get('page_size', 10)
    total = pagination.get('total_results', len(products))
    total_pages = pagination.get('total_pages', 1)
    has_next = page < total_pages

    display_text = f'Found {total} results for "{query}"'
    suggested_filters: list = []

    return {
        'products': products,
        'displayText': display_text,
        'suggestedFilters': suggested_filters,
        'total': total,
        'page': page,
        'page_size': page_size,
        'has_next': has_next,
    }
