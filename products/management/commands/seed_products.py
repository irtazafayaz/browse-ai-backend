"""
Management command: seed_products
Usage: python manage.py seed_products [--clear]

Seeds MongoDB with the initial product catalog matching the frontend mock data.
"""
from django.core.management.base import BaseCommand
from products.db import products_col

PRODUCTS = [
    {
        'id': 'p001', 'brand': 'Agolde', 'name': 'Cargo Wide-Leg Jeans',
        'imageUrl': 'https://images.unsplash.com/photo-1542272604-787c3835535d?w=400&h=500&fit=crop',
        'price': 198, 'originalPrice': 265,
        'tags': ['wide leg', 'cargo', 'denim', 'blue', 'jeans', 'pants'],
    },
    {
        'id': 'p002', 'brand': 'Toteme', 'name': 'Straight-Cut Trousers',
        'imageUrl': 'https://images.unsplash.com/photo-1594938298603-c8148c4b4d05?w=400&h=500&fit=crop',
        'price': 320, 'originalPrice': None,
        'tags': ['straight leg', 'trousers', 'tailored', 'black', 'pants'],
    },
    {
        'id': 'p003', 'brand': 'Aritzia', 'name': 'Effortless Pant',
        'imageUrl': 'https://images.unsplash.com/photo-1509631179647-0177331693ae?w=400&h=500&fit=crop',
        'price': 110, 'originalPrice': 148,
        'tags': ['relaxed fit', 'wide leg', 'beige', 'cream', 'pants', 'casual'],
    },
    {
        'id': 'p004', 'brand': 'Acne Studios', 'name': 'Loose-Fit Jeans',
        'imageUrl': 'https://images.unsplash.com/photo-1555689502-c4b22d76c56f?w=400&h=500&fit=crop',
        'price': 380, 'originalPrice': None,
        'tags': ['relaxed fit', 'loose', 'denim', 'blue', 'jeans', 'baggy'],
    },
    {
        'id': 'p005', 'brand': 'Reformation', 'name': 'Maroon High-Rise Jeans',
        'imageUrl': 'https://images.unsplash.com/photo-1604176354204-9268737828e4?w=400&h=500&fit=crop',
        'price': 158, 'originalPrice': None,
        'tags': ['maroon', 'burgundy', 'high rise', 'straight leg', 'jeans', 'colored'],
    },
    {
        'id': 'p006', 'brand': "Levi's", 'name': '501 Straight Jeans',
        'imageUrl': 'https://images.unsplash.com/photo-1542272604-787c3835535d?w=400&h=500&fit=crop&seed=6',
        'price': 89, 'originalPrice': None,
        'tags': ['straight leg', 'denim', 'blue', 'jeans', 'classic'],
    },
    {
        'id': 'p007', 'brand': 'Zara', 'name': 'Wide Leg Cargo Trousers',
        'imageUrl': 'https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=400&h=500&fit=crop',
        'price': 69, 'originalPrice': 99,
        'tags': ['wide leg', 'cargo', 'khaki', 'olive', 'trousers', 'pants'],
    },
    {
        'id': 'p008', 'brand': 'COS', 'name': 'Relaxed Pleated Trousers',
        'imageUrl': 'https://images.unsplash.com/photo-1506629082955-511b1aa562c8?w=400&h=500&fit=crop',
        'price': 125, 'originalPrice': None,
        'tags': ['relaxed fit', 'pleated', 'trousers', 'gray', 'grey', 'tailored'],
    },
    {
        'id': 'p009', 'brand': 'Mango', 'name': 'Burgundy Flared Pants',
        'imageUrl': 'https://images.unsplash.com/photo-1585487000160-6ebcfceb0d03?w=400&h=500&fit=crop',
        'price': 59, 'originalPrice': 79,
        'tags': ['flared', 'burgundy', 'maroon', 'red', 'pants', 'wide leg'],
    },
    {
        'id': 'p010', 'brand': 'H&M', 'name': 'Baggy Low-Rise Jeans',
        'imageUrl': 'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=400&h=500&fit=crop',
        'price': 39, 'originalPrice': None,
        'tags': ['baggy', 'low rise', 'denim', 'blue', 'jeans', 'relaxed fit'],
    },
    {
        'id': 'p011', 'brand': 'Frame', 'name': 'Le High Straight',
        'imageUrl': 'https://images.unsplash.com/photo-1594938298603-c8148c4b4d05?w=400&h=500&fit=crop&seed=11',
        'price': 245, 'originalPrice': None,
        'tags': ['straight leg', 'high rise', 'denim', 'blue', 'jeans', 'classic'],
    },
    {
        'id': 'p012', 'brand': 'Weekday', 'name': 'Barrel Leg Trousers',
        'imageUrl': 'https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=400&h=500&fit=crop',
        'price': 75, 'originalPrice': 95,
        'tags': ['barrel', 'wide leg', 'relaxed fit', 'beige', 'cream', 'trousers'],
    },
]


class Command(BaseCommand):
    help = 'Seed MongoDB products collection with initial data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing products before seeding',
        )

    def handle(self, *args, **options):
        col = products_col()

        if options['clear']:
            col.delete_many({})
            self.stdout.write(self.style.WARNING('Cleared existing products.'))

        inserted = 0
        skipped = 0
        for product in PRODUCTS:
            existing = col.find_one({'id': product['id']})
            if existing:
                skipped += 1
                continue
            col.insert_one(product)
            inserted += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done. Inserted {inserted} products, skipped {skipped} already existing.'
        ))
