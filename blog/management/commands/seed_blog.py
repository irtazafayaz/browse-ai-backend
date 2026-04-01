"""
Seed the blog_posts table with the initial 4 buying-guide articles.
Safe to run multiple times — skips slugs that already exist.

Usage:
    python manage.py seed_blog
"""
from datetime import datetime, timezone

from django.core.management.base import BaseCommand

from blog.models import BlogPost

POSTS = [
    {
        'slug': 'best-lawn-suit-brands',
        'title': "Best Pakistani Lawn Suit Brands: A Complete Buyer's Guide",
        'description': (
            "Looking for the best lawn suits in Pakistan? We compare Sana Safinaz, "
            "Gul Ahmed, Alkaram, and more — pricing, quality, and what to look for."
        ),
        'read_time': '7 min read',
        'category': 'Buying Guide',
        'cover_image': 'https://images.unsplash.com/photo-1733731402740-f0fd91bdd5c0?w=1200&q=80',
        'published_at': datetime(2025, 2, 10, tzinfo=timezone.utc),
        'content': """
<h2>Why Lawn Suits Dominate Pakistani Fashion</h2>
<p>Lawn fabric — a lightweight, breathable cotton weave — has become synonymous with Pakistani summer dressing. Each year, Pakistan's leading brands launch their lawn collections to massive fanfare, with prices ranging from affordable pret lines to premium hand-embroidered luxury pieces. If you're shopping for lawn suits online, knowing the difference between these brands will save you both time and money.</p>

<h2>Top Lawn Suit Brands Compared</h2>

<h3>Sana Safinaz</h3>
<p>Sana Safinaz is arguably Pakistan's most prestigious lawn brand. Their annual Muzlin and Signature collections are known for bold prints, clean silhouettes, and strong quality control. Expect to pay PKR 4,000–12,000 for an unstitched three-piece. Their fabric weight leans slightly heavier than competitors, making it ideal for the transitional months.</p>
<ul>
  <li><strong>Best for:</strong> Statement prints, gifting, formal occasions</li>
  <li><strong>Price range:</strong> Mid–premium</li>
  <li><strong>Ships internationally:</strong> Yes</li>
</ul>

<h3>Gul Ahmed</h3>
<p>Gul Ahmed's Ideas platform offers one of the broadest price ranges in the market — from basic single-piece kurtas under PKR 2,000 to embroidered luxury three-pieces above PKR 10,000. Their fabric is consistently soft and prints are vibrant. The Ideas brand also has physical stores across Pakistan, making returns straightforward.</p>
<ul>
  <li><strong>Best for:</strong> Everyday wear, value for money, wide variety</li>
  <li><strong>Price range:</strong> Budget–premium</li>
  <li><strong>Ships internationally:</strong> Yes</li>
</ul>

<h3>Alkaram Studio</h3>
<p>Alkaram is the go-to for trend-forward lawn at accessible prices. Their seasonal collections drop more frequently than most competitors, keeping the range fresh. Fabric quality is solid, and their embroidered lines punch well above their price point.</p>
<ul>
  <li><strong>Best for:</strong> Trendy buyers, budget-conscious shoppers</li>
  <li><strong>Price range:</strong> Budget–mid</li>
  <li><strong>Ships internationally:</strong> Yes</li>
</ul>

<h3>Maria B</h3>
<p>Maria B occupies the luxury end of the lawn market. Her M.Prints line uses digital printing on premium fabric with intricate embroidery details. If you're shopping for a special occasion or want something that photographs beautifully, Maria B is worth the premium.</p>
<ul>
  <li><strong>Best for:</strong> Weddings, formal dinners, gifting luxury</li>
  <li><strong>Price range:</strong> Premium–luxury</li>
  <li><strong>Ships internationally:</strong> Yes</li>
</ul>

<h2>What to Look for When Buying Lawn Online</h2>
<p>Before you click 'add to cart', check these four things:</p>
<ul>
  <li><strong>Thread count and GSM:</strong> Higher GSM (grams per square metre) means heavier fabric — better for cooler months. Summer lawn sits around 60–80 GSM.</li>
  <li><strong>Print type:</strong> Digital prints are vibrant but may fade faster. Screen-printed and reactive-dyed fabrics have better wash longevity.</li>
  <li><strong>Embroidery quality:</strong> Look for thread-work detail images, not just flat product shots. Cheap machine embroidery can fray quickly.</li>
  <li><strong>Dupatta fabric:</strong> A chiffon dupatta is more elegant; lawn or cotton dupatta is more practical for everyday wear.</li>
</ul>

<h2>Find Your Perfect Lawn Suit with Browse AI</h2>
<p>Instead of scrolling through each brand's website separately, try describing what you want in plain English. Browse AI searches across all major Pakistani fashion brands simultaneously — saving you hours of browsing.</p>
""",
    },
    {
        'slug': 'chiffon-dupatta-sets-guide',
        'title': 'Chiffon Dupatta Sets Under Rs 20,000: Where to Shop & What to Look For',
        'description': (
            'A practical guide to buying chiffon dupatta sets online — which Pakistani brands '
            'offer the best quality under Rs 20,000, and what to check before you buy.'
        ),
        'read_time': '6 min read',
        'category': 'Buying Guide',
        'cover_image': 'https://images.unsplash.com/photo-1617627143750-d86bc21e42bb?w=1200&q=80',
        'published_at': datetime(2025, 2, 24, tzinfo=timezone.utc),
        'content': """
<h2>The Appeal of Chiffon Dupatta Sets</h2>
<p>A chiffon dupatta instantly elevates any outfit. The fabric's natural drape and slight sheen make it a staple for both casual days and semi-formal occasions. When paired with a lawn or cotton kurta, it bridges the gap between everyday comfort and occasion-ready elegance — which is why chiffon dupatta sets consistently rank among the top-searched items in Pakistani online fashion.</p>

<h2>What Makes a Good Chiffon Dupatta?</h2>
<p>Not all chiffon is created equal. Here's what separates a quality piece from a fast-fashion disappointment:</p>
<ul>
  <li><strong>Weight:</strong> Quality chiffon has a fluid, weighted drape. If it feels stiff or crinkly in the product video, it likely won't drape well.</li>
  <li><strong>Print or embroidery:</strong> Printed chiffon (especially digital print) is more affordable; hand-embroidered or thread-work dupattas command a premium and last longer.</li>
  <li><strong>Width:</strong> A standard dupatta should be at least 100cm wide. Narrower cuts look skimpy and are harder to style.</li>
  <li><strong>Border detail:</strong> Scalloped edges, lace borders, or hand-stitched hemlines signal attention to craft.</li>
</ul>

<h2>Best Brands for Chiffon Dupatta Sets Under Rs 20,000</h2>

<h3>Limelight (Under Rs 8,000)</h3>
<p>Limelight's pret lines frequently include chiffon dupatta three-pieces at remarkable prices. Their summer collections offer printed chiffon dupattas that are ideal for daily wear. Don't expect luxury, but for everyday outfit needs, Limelight punches well above its price point.</p>

<h3>Nishat Linen (Under Rs 13,000)</h3>
<p>Nishat Linen is the sweet spot for quality-to-price ratio. Their N-Basics and seasonal lawn collections regularly feature chiffon dupatta sets with clean, wearable prints. Fabric is consistently soft, and the stitched options mean no tailoring needed.</p>

<h3>Generation (Rs 10,000–18,000)</h3>
<p>Generation takes a more fashion-forward approach. Their chiffon dupattas often feature block prints, abstract patterns, or contemporary motifs rather than traditional florals. A good choice if you want something that feels more modern.</p>

<h3>Sana Safinaz Muzlin (Rs 15,000–20,000)</h3>
<p>At the top of this price range, Sana Safinaz's Muzlin line offers chiffon dupattas that feel noticeably premium. The print quality, dupatta weight, and finishing details are a level above mass-market options. If you're buying for a special occasion, this is worth stretching to.</p>

<h2>Styling Tips</h2>
<ul>
  <li>Pair a heavily printed chiffon dupatta with a solid or subtly printed kurta — let the dupatta be the statement piece.</li>
  <li>For office wear, opt for a plain or lightly embroidered chiffon dupatta in a neutral tone.</li>
  <li>A side-drape (rather than over-the-shoulder) works best for casual settings and keeps the fabric off the floor.</li>
</ul>

<h2>Search Smarter</h2>
<p>Finding the right chiffon dupatta set used to mean visiting five different websites. With Browse AI, you can simply describe what you're looking for — "soft chiffon dupatta set in pastels under Rs 15,000" — and get results from across Pakistan's top brands instantly.</p>
""",
    },
    {
        'slug': 'pret-wear-pakistan-guide',
        'title': 'Pret Wear in Pakistan: Top Picks & Brands for 2025',
        'description': (
            "Ready-to-wear pret is transforming how Pakistani women shop. Here's our guide to "
            "the best pret brands, what to buy, and how to find great pieces without hours of browsing."
        ),
        'read_time': '5 min read',
        'category': 'Buying Guide',
        'cover_image': 'https://images.unsplash.com/photo-1558769132-cb1aea458c5e?w=1200&q=80',
        'published_at': datetime(2025, 3, 5, tzinfo=timezone.utc),
        'content': """
<h2>What Is Pret Wear?</h2>
<p>In Pakistani fashion, "pret" (short for prêt-à-porter, French for "ready to wear") refers to stitched, ready-to-wear outfits — as opposed to unstitched fabric that requires a tailor. The pret revolution in Pakistan has been driven by working women, younger consumers, and anyone who wants great style without the two-week wait for a tailor appointment.</p>

<h2>Pret vs. Unstitched: Which Is Right for You?</h2>
<ul>
  <li><strong>Choose pret if:</strong> You want to wear it immediately, you're buying as a gift, or you're shopping from abroad where local tailors aren't accessible.</li>
  <li><strong>Choose unstitched if:</strong> You want a custom fit, you prefer a specific silhouette, or you're buying premium fabric worth tailoring properly.</li>
</ul>
<p>For most modern lifestyles, pret wins on convenience. The trade-off is fit — standard sizes may not suit all body types, so check the brand's size chart carefully before ordering.</p>

<h2>The Best Pret Brands in Pakistan Right Now</h2>

<h3>Bonanza Satrangi</h3>
<p>Bonanza Satrangi has built one of Pakistan's strongest pret businesses by combining bold colour palettes with accessible prices. Their stitched kurtas and co-ord sets photograph exceptionally well — you'll recognise their aesthetic immediately on social media. Great for casual-to-smart-casual occasions.</p>

<h3>Limelight</h3>
<p>Limelight is the volume player in Pakistani pret. They release new designs almost weekly, keeping their catalogue fresh. Quality is consistent if not exceptional, and prices are among the lowest for stitched outfits. If you're building an everyday wardrobe on a budget, start here.</p>

<h3>Generation</h3>
<p>Generation has a distinct creative identity that sets it apart from the crowd. Their pret lines draw on Pakistani craft traditions — block printing, hand embroidery, natural dyes — and combine them with contemporary silhouettes. Pricier than Limelight, but the craftsmanship justifies the premium.</p>

<h3>Alkaram Studio Pret</h3>
<p>Alkaram's stitched line offers good middle-ground quality at moderate prices. Their seasonal drops align with fashion trends while staying rooted in wearable Pakistani silhouettes. A reliable choice if you want something between mass-market and boutique.</p>

<h2>What to Check Before Buying Pret Online</h2>
<ul>
  <li><strong>Measurements:</strong> Read the brand's size guide, not just S/M/L labels — Pakistani brands vary significantly in cut.</li>
  <li><strong>Return policy:</strong> Pret is harder to alter than unstitched, so check if the brand accepts returns or exchanges before ordering.</li>
  <li><strong>Fabric composition:</strong> Cotton and linen pret breathes better; polyester blends wrinkle less but can feel hot in summer.</li>
  <li><strong>Care instructions:</strong> Hand-embroidered pieces often require gentle hand wash — factor this into your decision.</li>
</ul>

<h2>Find Pret Wear Instantly</h2>
<p>Browse AI lets you search across all major Pakistani pret brands with a single natural-language query. Try "stitched kurta in earthy tones under PKR 3,000" and see results from Limelight, Generation, Bonanza, and more — all in one place.</p>
""",
    },
    {
        'slug': 'pakistani-wedding-guest-outfits',
        'title': 'Pakistani Wedding Guest Outfits: The Complete Buying Guide',
        'description': (
            'Attending a Pakistani wedding and not sure what to wear? This guide covers every event '
            '— dholki, mehndi, baraat, and valima — with brand recommendations and budget tips.'
        ),
        'read_time': '8 min read',
        'category': 'Buying Guide',
        'cover_image': 'https://images.unsplash.com/photo-1627205265923-190841d62452?w=1200&q=80',
        'published_at': datetime(2025, 3, 12, tzinfo=timezone.utc),
        'content': """
<h2>Understanding Pakistani Wedding Events</h2>
<p>Pakistani weddings are multi-day affairs, each with its own dress code and vibe. Getting the occasion right matters — showing up in bridal-level finery at a dholki or arriving in casual pret to a formal baraat are both easy mistakes to make. Here's a breakdown of each event and what to wear.</p>

<h2>Dholki: Colourful &amp; Fun</h2>
<p>The dholki is the most casual of the wedding events — music, dancing, close friends and family. The vibe is festive but relaxed.</p>
<ul>
  <li><strong>What works:</strong> Vibrant colours, printed lawn or cotton three-pieces, casual chiffon dupatta sets, embroidered pret kurtas</li>
  <li><strong>What to avoid:</strong> Heavy bridal colours (red, gold), overly formal chiffon or georgette, excessive jewellery</li>
  <li><strong>Budget range:</strong> PKR 3,000–8,000</li>
  <li><strong>Brands to check:</strong> Bonanza Satrangi, Limelight, Alkaram pret</li>
</ul>

<h2>Mehndi: Bold Colours, Heavy Prints</h2>
<p>The mehndi is the big dress-up moment before the baraat. Yellows, oranges, greens, and pinks dominate. This is the event for statement outfits.</p>
<ul>
  <li><strong>What works:</strong> Bright embroidered three-pieces, tissue or organza dupattas, embellished suits with gota work or tilla borders</li>
  <li><strong>What to avoid:</strong> Whites, blacks, and heavy reds (save these for baraat)</li>
  <li><strong>Budget range:</strong> PKR 8,000–20,000</li>
  <li><strong>Brands to check:</strong> Sana Safinaz formal, Maria B pret, Nishat formal collection</li>
</ul>

<h2>Baraat (Wedding Ceremony): Your Most Formal Look</h2>
<p>The baraat is the main wedding event. Guests are expected to dress formally — this is where chiffon, georgette, and velvet have their moment.</p>
<ul>
  <li><strong>What works:</strong> Embroidered chiffon or net three-pieces, formal anarkali styles, rich colours like burgundy, navy, emerald, and gold</li>
  <li><strong>What to avoid:</strong> Bridal red/white (never upstage the bride), overly casual prints</li>
  <li><strong>Budget range:</strong> PKR 15,000–40,000</li>
  <li><strong>Brands to check:</strong> Maria B luxury pret, Sana Safinaz formal, boutique options</li>
</ul>

<h2>Valima (Reception): Elegant &amp; Refined</h2>
<p>The valima tends to be more refined than the baraat. Pastels, soft embroidery, and understated elegance work best.</p>
<ul>
  <li><strong>What works:</strong> Soft chiffon or silk in pastels, subtly embroidered three-pieces, co-ord sets in neutral tones</li>
  <li><strong>Budget range:</strong> PKR 8,000–20,000</li>
  <li><strong>Brands to check:</strong> Nishat Linen formal, Generation, Gul Ahmed formal</li>
</ul>

<h2>Smart Shopping Tips for Wedding Season</h2>
<ul>
  <li><strong>Buy early:</strong> Popular formal designs sell out 3–4 weeks before peak wedding season (Oct–Dec and April–June).</li>
  <li><strong>Budget for tailoring:</strong> If buying unstitched, add PKR 2,000–5,000 for a good tailor on top of the fabric price.</li>
  <li><strong>Check for colour-run risk:</strong> Deeply dyed fabrics (especially navy and black) can bleed on lighter dupattas — ask the retailer or test on a hidden seam.</li>
  <li><strong>Mix events smartly:</strong> A strong mehndi outfit with a different dupatta can double as valima wear — saves budget without sacrificing style.</li>
</ul>

<h2>Find Your Wedding Guest Outfit in Seconds</h2>
<p>Instead of browsing a dozen websites, describe your dream outfit to Browse AI. Try "embroidered chiffon three-piece in dusty rose for a baraat" or "bright mehndi outfit under PKR 10,000" — and get curated results from across Pakistan's top brands instantly.</p>
""",
    },
]


class Command(BaseCommand):
    help = 'Seed the blog_posts table with initial buying-guide articles.'

    def handle(self, *args, **options):
        created = 0
        skipped = 0

        for post_data in POSTS:
            slug = post_data['slug']
            if BlogPost.objects.filter(slug=slug).exists():
                self.stdout.write(f'  skip  {slug}')
                skipped += 1
                continue

            BlogPost.objects.create(**post_data)
            self.stdout.write(self.style.SUCCESS(f'  created  {slug}'))
            created += 1

        self.stdout.write(
            self.style.SUCCESS(f'\nDone — {created} created, {skipped} skipped.')
        )
