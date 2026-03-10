"""
Management command: seed_edits
Usage: python manage.py seed_edits [--clear]

Seeds MongoDB with curated editorial collections and search prompts.
"""
from django.core.management.base import BaseCommand
from products.db import get_db

EDITS = [
    {'label': 'Wide Leg', 'imageUrl': 'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=600&h=800&fit=crop', 'tag': 'Trending'},
    {'label': 'Maroon & Burgundy', 'imageUrl': 'https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=600&h=800&fit=crop', 'tag': 'Color Story'},
    {'label': 'Cargo Everything', 'imageUrl': 'https://images.unsplash.com/photo-1617137984095-74e4e5e3613f?w=600&h=800&fit=crop', 'tag': 'Street'},
    {'label': 'Straight Leg', 'imageUrl': 'https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=600&h=800&fit=crop', 'tag': 'Classic'},
    {'label': 'Relaxed Fit', 'imageUrl': 'https://images.unsplash.com/photo-1544957992-20514f595d6f?w=600&h=800&fit=crop', 'tag': 'Casual'},
    {'label': 'High Rise', 'imageUrl': 'https://images.unsplash.com/photo-1566206091558-7f218b696731?w=600&h=800&fit=crop', 'tag': 'Editorial'},
]

PROMPTS = [
    {'text': 'baggy linen pants in earthy tones...'},
    {'text': 'something maroon and wide leg...'},
    {'text': 'cargo pants with a relaxed fit...'},
    {'text': 'straight leg jeans, classic blue...'},
    {'text': 'elevated basics under $100...'},
    {'text': 'oversized and effortless...'},
]


class Command(BaseCommand):
    help = 'Seed MongoDB edits and prompts collections'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing data before seeding')

    def handle(self, *args, **options):
        db = get_db()

        for col_name, data in [('edits', EDITS), ('prompts', PROMPTS)]:
            col = db[col_name]
            if options['clear']:
                col.delete_many({})
                self.stdout.write(self.style.WARNING(f'Cleared {col_name}.'))
            if col.count_documents({}) == 0:
                col.insert_many(data)
                self.stdout.write(self.style.SUCCESS(f'Inserted {len(data)} {col_name}.'))
            else:
                self.stdout.write(f'{col_name}: already seeded, skipping.')
