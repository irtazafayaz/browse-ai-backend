# Search Overhaul Plan

## What changes
- Remove chatbot (ChatPanel, chat history, AI display text) entirely
- Add text search + image search, both on the Results page
- Add pagination (infinite scroll) to product list
- Add filters (brand, price range, tags)
- Backend: stub image-search endpoint; AI service wired later

---

## Backend (3 files)

### 1. `products/views.py`
**Update `product_list`**:
- Add pagination: `?page=1&page_size=24`
- Add filters: `?brand=Levi%27s&min_price=50&max_price=150&tags=slim,blue`
- Return `{ products, total, page, has_next, page_size }`

**Add `image_search` view** (`POST /api/products/image-search/`):
- Accept multipart form with `image` field (File)
- Stub: return paginated products from MongoDB (comment marks where AI goes)
- Same response shape as `product_list`

### 2. `products/urls.py`
- Add `path('image-search/', views.image_search, name='image-search')` BEFORE `<str:product_id>/`

### 3. `products/serializers.py`
- No changes needed

---

## Frontend (5 files, 1 new component)

### 1. `src/lib/types.ts`
Add:
```ts
interface SearchFilters { brand?: string; minPrice?: number; maxPrice?: number; tags?: string[] }
interface PaginatedProducts { products: Product[]; total: number; page: number; has_next: boolean }
```
Remove: `ChatMessage`, `AiResponse`, `FilterChip` (no longer used)

### 2. `src/lib/api.ts`
- Update `getProducts(params)`: accept `{ q?, page?, brand?, min_price?, max_price?, tags? }` → returns `PaginatedProducts`
- Remove `searchProducts()` (chat-based, no longer needed)
- Add `searchByImage(file, page?)` → `POST /api/products/image-search/` multipart → `PaginatedProducts`

### 3. `src/components/FilterDrawer.tsx` (new)
- Filter button shows badge with count of active filters
- Opens a slide-up drawer (mobile & desktop)
- Sections: Brand (checkboxes from `getBrands()`), Price range (min/max), Tags (common chips)
- Apply / Clear all buttons
- Calls `onChange(filters)` callback

### 4. `src/app/results/page.tsx` — full rewrite
Layout:
```
┌─ Sticky TopBar ─────────────────────────────────┐
│ ← Browse AI        [Filters] [bookmarks] [auth] │
├─ Sticky SearchSection ──────────────────────────┤
│ [Text] [Image] tabs                             │
│ Text: [ search input .................. → ]      │
│ Image: [ drag & drop / click to upload zone ]   │
│         (shows thumbnail preview when loaded)   │
├─ SortFilterBar ─────────────────────────────────┤
│ 42 results  [active filter chips ×]             │
│ [Best match] [Trending] [Price ↑] [Price ↓]    │
└─ MasonryGrid ───────────────────────────────────┘
  [product cards...]
  [loading skeletons when fetching next page]
  [sentinel div — IntersectionObserver target]
```

State:
- `mode: 'text' | 'image'`
- `query: string` (from URL `?q=`)
- `imageFile: File | null`, `imagePreview: string | null`
- `products: Product[]`, `page: number`, `hasNext: boolean`
- `loading: boolean`, `loadingMore: boolean`
- `filters: SearchFilters`, `sort: SortMode`
- `filterDrawerOpen: boolean`

Infinite scroll: IntersectionObserver on sentinel div → calls `loadNextPage()` when visible and `hasNext && !loadingMore`

Image upload: drag-and-drop OR click-to-open file picker (accept="image/*") → preview thumbnail → auto-trigger search

### 5. `src/app/page.tsx`
- Keep home page SearchBar as text-only (clean hero stays)
- Navigates to `/results?q=...` as before
- No changes needed unless home page also needs image tab (out of scope per user choice)
