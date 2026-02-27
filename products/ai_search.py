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


def _extract_filters_with_ai(query: str, history: list) -> tuple[list[str], str]:
    """
    Ask Claude to extract filter tags from the user's query.
    Returns (filter_tags, display_text).
    Falls back to splitting query words if no API key configured.
    """
    if not settings.ANTHROPIC_API_KEY:
        # Simple fallback — split query into words as filters
        words = [w.lower().strip('.,!?') for w in query.split() if len(w) > 2]
        display = f'Found results for "{query}"'
        return words, display

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

    # Build conversation history
    messages = []
    for msg in history[-6:]:  # last 6 messages for context
        role = 'user' if msg.get('sender') == 'user' else 'assistant'
        messages.append({'role': role, 'content': msg.get('text', '')})

    messages.append({'role': 'user', 'content': query})

    response = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=256,
        system=system_prompt,
        messages=messages,
    )

    raw = response.content[0].text.strip()

    # Extract JSON even if Claude wraps it in markdown
    json_match = re.search(r'\{.*\}', raw, re.DOTALL)
    if json_match:
        data = json.loads(json_match.group())
        return data.get('filters', []), data.get('displayText', f'Results for "{query}"')

    # Parsing failed — fall back
    words = [w.lower() for w in query.split() if len(w) > 2]
    return words, f'Results for "{query}"'


def search_products(query: str, history: list, user_id=None) -> dict:
    """
    Main search function called by the view.
    Returns { products, displayText, suggestedFilters }.
    """
    filters, display_text = _extract_filters_with_ai(query, history)

    col = products_col()

    if filters:
        # Match products whose tags array contains any of the filter words
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

    # Attach isBookmarked flag if user is logged in
    bookmarked_ids = set()
    if user_id:
        bmarks = bookmarks_col().find({'user_id': str(user_id)})
        bookmarked_ids = {b['product_id'] for b in bmarks}

    products = []
    for doc in docs:
        product_id = str(doc['_id'])
        products.append({
            '_id_str': doc.get('id', product_id),
            'brand': doc.get('brand', ''),
            'name': doc.get('name', ''),
            'imageUrl': doc.get('imageUrl', ''),
            'price': doc.get('price', 0),
            'originalPrice': doc.get('originalPrice'),
            'tags': doc.get('tags', []),
            'isBookmarked': doc.get('id', product_id) in bookmarked_ids,
        })

    return {
        'products': products,
        'displayText': display_text,
        'suggestedFilters': filters,
    }
