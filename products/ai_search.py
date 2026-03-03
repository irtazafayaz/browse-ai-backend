"""
AI-powered search helper.
Sends the user query to Anthropic Claude to extract filter keywords,
then queries MongoDB for matching products.
Falls back to simple keyword matching if no API key is set.
"""
import json
import re

from django.conf import settings

from .db import products_col, bookmarks_col
from .utils import doc_to_product


def _extract_filters_with_ai(query: str, history: list) -> tuple[list[str], str]:
    """
    Ask Claude to extract filter tags from the user's query.
    Returns (filter_tags, display_text).
    Falls back to keyword splitting if no API key is configured or on error.
    """
    if not settings.ANTHROPIC_API_KEY:
        words = [w.lower().strip('.,!?') for w in query.split() if len(w) > 2]
        return words, f'Found results for "{query}"'

    import anthropic

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    system_prompt = (
        'You are a fashion search assistant. The user describes clothing they want. '
        'Extract a list of relevant filter tags (lowercase, short phrases like "wide leg", "cargo", '
        '"denim", "blue", "high rise") from their query. '
        'Also write a short friendly one-sentence response acknowledging their search. '
        'Respond ONLY with valid JSON in this exact shape: '
        '{"filters": ["tag1", "tag2"], "displayText": "..."}'
    )

    messages = []
    for msg in history[-6:]:
        role = 'user' if msg.get('sender') == 'user' else 'assistant'
        messages.append({'role': role, 'content': msg.get('text', '')})
    messages.append({'role': 'user', 'content': query})

    try:
        response = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=256,
            system=system_prompt,
            messages=messages,
        )
        raw = response.content[0].text.strip()
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            return data.get('filters', []), data.get('displayText', f'Results for "{query}"')
    except (anthropic.APIError, json.JSONDecodeError, IndexError):
        pass

    words = [w.lower().strip('.,!?') for w in query.split() if len(w) > 2]
    return words, f'Results for "{query}"'


def search_products(query: str, history: list, user_id=None) -> dict:
    """
    Main search function called by the view.
    Returns { products, displayText, suggestedFilters }.
    """
    filters, display_text = _extract_filters_with_ai(query, history)

    col = products_col()

    if filters:
        mongo_filter = {
            'tags': {
                '$elemMatch': {
                    '$regex': '|'.join(re.escape(f) for f in filters),
                    '$options': 'i',
                }
            }
        }
        docs = list(col.find(mongo_filter))
    else:
        docs = list(col.find())

    bookmarked_ids = set()
    if user_id:
        bookmarked_ids = {b['product_id'] for b in bookmarks_col().find({'user_id': str(user_id)})}

    return {
        'products': [doc_to_product(doc, bookmarked_ids) for doc in docs],
        'displayText': display_text,
        'suggestedFilters': filters,
    }
