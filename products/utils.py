def doc_to_product(doc: dict, bookmarked_ids: set = None) -> dict:
    """Convert a MongoDB product document to the frontend Product shape."""
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
