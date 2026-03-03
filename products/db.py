# Re-export from core.db for backwards compatibility within the products app.
from core.db import get_db, products_col, bookmarks_col, edits_col, prompts_col

__all__ = ['get_db', 'products_col', 'bookmarks_col', 'edits_col', 'prompts_col']
