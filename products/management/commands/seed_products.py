"""
Management command: seed_products
Usage:
    python manage.py seed_products            # insert only new products
    python manage.py seed_products --clear    # wipe collection first, then insert
"""
from django.core.management.base import BaseCommand
from products.db import products_col

# ─────────────────────────────────────────────────────────────────
#  Only the 10 curated Pakistani fashion brands
# ─────────────────────────────────────────────────────────────────
PRODUCTS = [

    # ── Sana Safinaz ──────────────────────────────────────────────
    {
        'id': 'ss001', 'brand': 'Sana Safinaz', 'name': 'Embroidered Lawn 3-Piece Suit',
        'imageUrl': 'https://images.unsplash.com/photo-1583391733956-6c78276477e2?w=400&h=500&fit=crop',
        'price': 48, 'originalPrice': 65,
        'tags': ['lawn', 'embroidered', 'suit', '3-piece', 'floral', 'summer', 'women'],
    },
    {
        'id': 'ss002', 'brand': 'Sana Safinaz', 'name': 'Luxury Chiffon Formal Suit',
        'imageUrl': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=500&fit=crop',
        'price': 130, 'originalPrice': 170,
        'tags': ['chiffon', 'formal', 'luxury', 'embroidered', 'party', 'women'],
    },
    {
        'id': 'ss003', 'brand': 'Sana Safinaz', 'name': 'Printed Cambric Casual Shirt',
        'imageUrl': 'https://images.unsplash.com/photo-1485968579580-b6d095142e6e?w=400&h=500&fit=crop',
        'price': 28, 'originalPrice': None,
        'tags': ['cambric', 'printed', 'casual', 'shirt', 'daily wear', 'women'],
    },

    # ── Alkaram Studio ────────────────────────────────────────────
    {
        'id': 'ak001', 'brand': 'Alkaram Studio', 'name': 'Floral Digital Print Lawn Suit',
        'imageUrl': 'https://images.unsplash.com/photo-1572804013427-4d7ca7268217?w=400&h=500&fit=crop',
        'price': 35, 'originalPrice': 48,
        'tags': ['lawn', 'floral', 'digital print', 'summer', 'suit', 'women'],
    },
    {
        'id': 'ak002', 'brand': 'Alkaram Studio', 'name': 'Embroidered Stitched Pret',
        'imageUrl': 'https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?w=400&h=500&fit=crop',
        'price': 72, 'originalPrice': 95,
        'tags': ['stitched', 'embroidered', 'pret', 'kurta', 'women'],
    },
    {
        'id': 'ak003', 'brand': 'Alkaram Studio', 'name': 'Casual Khaddar Winter Suit',
        'imageUrl': 'https://images.unsplash.com/photo-1609505848912-b7c3b8b4beda?w=400&h=500&fit=crop',
        'price': 42, 'originalPrice': None,
        'tags': ['khaddar', 'winter', 'casual', 'suit', 'warm', 'women'],
    },

    # ── Gul Ahmed ─────────────────────────────────────────────────
    {
        'id': 'ga001', 'brand': 'Gul Ahmed', 'name': 'Ideas Pure Cotton Lawn Suit',
        'imageUrl': 'https://images.unsplash.com/photo-1523381294911-8d3cead13475?w=400&h=500&fit=crop',
        'price': 38, 'originalPrice': 52,
        'tags': ['lawn', 'cotton', 'ideas', 'summer', 'suit', 'women'],
    },
    {
        'id': 'ga002', 'brand': 'Gul Ahmed', 'name': 'Embroidered Chiffon Wedding Suit',
        'imageUrl': 'https://images.unsplash.com/photo-1566479179817-c4a0bafe5b5e?w=400&h=500&fit=crop',
        'price': 110, 'originalPrice': 145,
        'tags': ['chiffon', 'embroidered', 'wedding', 'formal', 'party', 'women'],
    },
    {
        'id': 'ga003', 'brand': 'Gul Ahmed', 'name': 'Men\'s Premium Oxford Shirt',
        'imageUrl': 'https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=400&h=500&fit=crop',
        'price': 30, 'originalPrice': None,
        'tags': ['shirt', 'oxford', 'men', 'formal', 'casual', 'cotton'],
    },

    # ── Nishat Linen ──────────────────────────────────────────────
    {
        'id': 'nl001', 'brand': 'Nishat Linen', 'name': 'Digital Printed Lawn Collection',
        'imageUrl': 'https://images.unsplash.com/photo-1612336307429-8a898d10e223?w=400&h=500&fit=crop',
        'price': 45, 'originalPrice': 60,
        'tags': ['lawn', 'digital print', 'collection', 'summer', 'women'],
    },
    {
        'id': 'nl002', 'brand': 'Nishat Linen', 'name': 'Embroidered Net Formal Suit',
        'imageUrl': 'https://images.unsplash.com/photo-1571513722275-4ad9f29e5476?w=400&h=500&fit=crop',
        'price': 145, 'originalPrice': 190,
        'tags': ['net', 'embroidered', 'formal', 'luxury', 'party wear', 'women'],
    },
    {
        'id': 'nl003', 'brand': 'Nishat Linen', 'name': 'Casual Linen Co-ord Set',
        'imageUrl': 'https://images.unsplash.com/photo-1509631179647-0177331693ae?w=400&h=500&fit=crop',
        'price': 55, 'originalPrice': None,
        'tags': ['linen', 'co-ord', 'casual', 'set', 'relaxed', 'women'],
    },

    # ── Maria B ───────────────────────────────────────────────────
    {
        'id': 'mb001', 'brand': 'Maria B', 'name': 'Luxury Embroidered Lawn Suit',
        'imageUrl': 'https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=400&h=500&fit=crop',
        'price': 88, 'originalPrice': 115,
        'tags': ['lawn', 'embroidered', 'luxury', 'suit', 'summer', 'women'],
    },
    {
        'id': 'mb002', 'brand': 'Maria B', 'name': 'Mbroidered Chiffon Maxi Dress',
        'imageUrl': 'https://images.unsplash.com/photo-1574201635302-388dd92a4c3f?w=400&h=500&fit=crop',
        'price': 195, 'originalPrice': 250,
        'tags': ['maxi', 'dress', 'chiffon', 'embroidered', 'formal', 'women'],
    },
    {
        'id': 'mb003', 'brand': 'Maria B', 'name': 'Ready-to-Wear Kurta Set',
        'imageUrl': 'https://images.unsplash.com/photo-1583391733956-6c78276477e2?w=400&h=500&fit=crop&seed=mb003',
        'price': 70, 'originalPrice': 95,
        'tags': ['kurta', 'pret', 'ready to wear', 'casual', 'women'],
    },

    # ── Limelight ─────────────────────────────────────────────────
    {
        'id': 'll001', 'brand': 'Limelight', 'name': 'Printed Pret Kurti',
        'imageUrl': 'https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=400&h=500&fit=crop&seed=ll001',
        'price': 22, 'originalPrice': 30,
        'tags': ['kurti', 'printed', 'pret', 'casual', 'daily wear', 'women'],
    },
    {
        'id': 'll002', 'brand': 'Limelight', 'name': 'Embroidered Shirt with Trousers',
        'imageUrl': 'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=400&h=500&fit=crop',
        'price': 45, 'originalPrice': 58,
        'tags': ['embroidered', 'shirt', 'trousers', 'set', 'pret', 'women'],
    },
    {
        'id': 'll003', 'brand': 'Limelight', 'name': 'Casual Knit Sweater',
        'imageUrl': 'https://images.unsplash.com/photo-1576566588405-571ebb1d3ca7?w=400&h=500&fit=crop',
        'price': 38, 'originalPrice': None,
        'tags': ['sweater', 'knit', 'casual', 'winter', 'warm', 'women'],
    },

    # ── Generation ────────────────────────────────────────────────
    {
        'id': 'gn001', 'brand': 'Generation', 'name': 'Handblock Printed Kameez',
        'imageUrl': 'https://images.unsplash.com/photo-1583391733956-6c78276477e2?w=400&h=500&fit=crop&seed=gn001',
        'price': 40, 'originalPrice': 52,
        'tags': ['handblock', 'printed', 'kameez', 'artisan', 'cotton', 'women'],
    },
    {
        'id': 'gn002', 'brand': 'Generation', 'name': 'Khadi Organic Cotton Shirt',
        'imageUrl': 'https://images.unsplash.com/photo-1489987707025-afc232f7ea0f?w=400&h=500&fit=crop',
        'price': 35, 'originalPrice': None,
        'tags': ['khadi', 'organic', 'cotton', 'shirt', 'sustainable', 'unisex'],
    },
    {
        'id': 'gn003', 'brand': 'Generation', 'name': 'Block-Dyed Wide-Leg Trousers',
        'imageUrl': 'https://images.unsplash.com/photo-1506629082955-511b1aa562c8?w=400&h=500&fit=crop',
        'price': 48, 'originalPrice': 62,
        'tags': ['wide leg', 'trousers', 'block dyed', 'artisan', 'relaxed', 'women'],
    },

    # ── Bonanza Satrangi ──────────────────────────────────────────
    {
        'id': 'bn001', 'brand': 'Bonanza Satrangi', 'name': 'Embroidered Lawn Suit',
        'imageUrl': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=500&fit=crop&seed=bn001',
        'price': 40, 'originalPrice': 55,
        'tags': ['lawn', 'embroidered', 'suit', 'summer', 'floral', 'women'],
    },
    {
        'id': 'bn002', 'brand': 'Bonanza Satrangi', 'name': 'Striped Cotton Polo Shirt',
        'imageUrl': 'https://images.unsplash.com/photo-1602810316693-3667c854239a?w=400&h=500&fit=crop',
        'price': 28, 'originalPrice': None,
        'tags': ['polo', 'striped', 'cotton', 'casual', 'men', 'shirt'],
    },
    {
        'id': 'bn003', 'brand': 'Bonanza Satrangi', 'name': 'Cable Knit Crew Neck Sweater',
        'imageUrl': 'https://images.unsplash.com/photo-1608234808654-2a8875faa7fd?w=400&h=500&fit=crop',
        'price': 55, 'originalPrice': 72,
        'tags': ['sweater', 'cable knit', 'crewneck', 'winter', 'warm', 'unisex'],
    },

    # ── ONE ───────────────────────────────────────────────────────
    {
        'id': 'on001', 'brand': 'ONE', 'name': 'Contemporary Structured Blazer',
        'imageUrl': 'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=400&h=500&fit=crop',
        'price': 85, 'originalPrice': 110,
        'tags': ['blazer', 'structured', 'contemporary', 'tailored', 'women', 'jacket'],
    },
    {
        'id': 'on002', 'brand': 'ONE', 'name': 'Minimal Wide-Leg Linen Trousers',
        'imageUrl': 'https://images.unsplash.com/photo-1509631179647-0177331693ae?w=400&h=500&fit=crop&seed=on002',
        'price': 65, 'originalPrice': None,
        'tags': ['linen', 'wide leg', 'trousers', 'minimal', 'women', 'casual'],
    },
    {
        'id': 'on003', 'brand': 'ONE', 'name': 'Relaxed Linen Co-ord Set',
        'imageUrl': 'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=400&h=500&fit=crop&seed=on003',
        'price': 90, 'originalPrice': 120,
        'tags': ['co-ord', 'linen', 'relaxed', 'set', 'casual', 'women'],
    },

    # ── Engine ────────────────────────────────────────────────────
    {
        'id': 'en001', 'brand': 'Engine', 'name': 'Classic Slim Fit Oxford Shirt',
        'imageUrl': 'https://images.unsplash.com/photo-1607345366928-199ea26cfe3e?w=400&h=500&fit=crop',
        'price': 42, 'originalPrice': 55,
        'tags': ['oxford', 'slim fit', 'shirt', 'men', 'formal', 'classic'],
    },
    {
        'id': 'en002', 'brand': 'Engine', 'name': 'Slim Fit Stretch Chinos',
        'imageUrl': 'https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=400&h=500&fit=crop',
        'price': 52, 'originalPrice': 68,
        'tags': ['chinos', 'slim fit', 'stretch', 'men', 'casual', 'trousers'],
    },
    {
        'id': 'en003', 'brand': 'Engine', 'name': 'Premium Linen Summer Shirt',
        'imageUrl': 'https://images.unsplash.com/photo-1489987707025-afc232f7ea0f?w=400&h=500&fit=crop&seed=en003',
        'price': 38, 'originalPrice': None,
        'tags': ['linen', 'summer', 'shirt', 'men', 'casual', 'breathable'],
    },
]


class Command(BaseCommand):
    help = 'Seed MongoDB with 10 curated Pakistani brand products'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear ALL existing products before seeding',
        )

    def handle(self, *args, **options):
        col = products_col()

        if options['clear']:
            deleted = col.delete_many({}).deleted_count
            self.stdout.write(self.style.WARNING(f'Cleared {deleted} existing products.'))

        inserted = skipped = 0
        for product in PRODUCTS:
            if col.find_one({'id': product['id']}):
                skipped += 1
            else:
                col.insert_one(product)
                inserted += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done. Inserted {inserted} products, skipped {skipped} already existing.'
        ))
