"""Run from project root: python seed_data/seed.py"""
import os
import sys
import shutil
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, ClothingItem

SEED_ITEMS = [
    {
        'name': 'White Oxford Shirt',
        'category': 'top',
        'color_primary': 'white',
        'style_tags': 'smart-casual,formal',
        'season': 'all',
        'image_url': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400',
        'filename': 'white_oxford.jpg',
    },
    {
        'name': 'Grey T-Shirt',
        'category': 'top',
        'color_primary': 'grey',
        'style_tags': 'casual',
        'season': 'all',
        'image_url': 'https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=400',
        'filename': 'grey_tshirt.jpg',
    },
    {
        'name': 'Blue Hoodie',
        'category': 'top',
        'color_primary': 'blue',
        'style_tags': 'casual,sporty',
        'season': 'all',
        'image_url': 'https://images.unsplash.com/photo-1556821840-3a63f15732ce?w=400',
        'filename': 'blue_hoodie.jpg',
    },
    {
        'name': 'Navy Polo Shirt',
        'category': 'top',
        'color_primary': 'navy',
        'style_tags': 'smart-casual',
        'season': 'all',
        'image_url': 'https://images.unsplash.com/photo-1586790170083-2f9ceadc732d?w=400',
        'filename': 'navy_polo.jpg',
    },
    {
        'name': 'Navy Chinos',
        'category': 'bottom',
        'color_primary': 'navy',
        'style_tags': 'smart-casual,casual',
        'season': 'all',
        'image_url': 'https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=400',
        'filename': 'navy_chinos.jpg',
    },
    {
        'name': 'Black Jeans',
        'category': 'bottom',
        'color_primary': 'black',
        'style_tags': 'casual',
        'season': 'all',
        'image_url': 'https://images.unsplash.com/photo-1542272604-787c3835535d?w=400',
        'filename': 'black_jeans.jpg',
    },
    {
        'name': 'Beige Chinos',
        'category': 'bottom',
        'color_primary': 'beige',
        'style_tags': 'casual,smart-casual',
        'season': 'all',
        'image_url': 'https://images.unsplash.com/photo-1594938298603-c8148c4b4616?w=400',
        'filename': 'beige_chinos.jpg',
    },
    {
        'name': 'White Sneakers',
        'category': 'shoes',
        'color_primary': 'white',
        'style_tags': 'casual,smart-casual',
        'season': 'all',
        'image_url': 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400',
        'filename': 'white_sneakers.jpg',
    },
    {
        'name': 'Black Leather Boots',
        'category': 'shoes',
        'color_primary': 'black',
        'style_tags': 'smart-casual,formal',
        'season': 'all',
        'image_url': 'https://images.unsplash.com/photo-1608256246200-53e635b5b65f?w=400',
        'filename': 'black_boots.jpg',
    },
    {
        'name': 'Black Jacket',
        'category': 'outerwear',
        'color_primary': 'black',
        'style_tags': 'casual,smart-casual',
        'season': 'spring-fall',
        'image_url': 'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=400',
        'filename': 'black_jacket.jpg',
    },
]

FALLBACK_URL_TEMPLATE = 'https://picsum.photos/seed/{seed}/400/500'


def download_image(url, dest_path, fallback_url=None):
    headers = {'User-Agent': 'ClothsAI/1.0'}
    try:
        resp = requests.get(url, stream=True, timeout=15, headers=headers)
        resp.raise_for_status()
        with open(dest_path, 'wb') as f:
            shutil.copyfileobj(resp.raw, f)
        return True
    except Exception as e:
        if fallback_url:
            print(f"  Primary URL failed ({e}), trying fallback...")
            try:
                resp = requests.get(fallback_url, stream=True, timeout=15, headers=headers)
                resp.raise_for_status()
                with open(dest_path, 'wb') as f:
                    shutil.copyfileobj(resp.raw, f)
                return True
            except Exception as e2:
                raise Exception(f"Both primary and fallback failed: {e2}") from e2
        raise


def seed():
    uploads_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads'
    )
    os.makedirs(uploads_dir, exist_ok=True)

    with app.app_context():
        db.create_all()
        ClothingItem.query.delete()
        db.session.commit()

        for data in SEED_ITEMS:
            dest = os.path.join(uploads_dir, data['filename'])
            if not os.path.exists(dest):
                print(f"Downloading {data['name']}...")
                seed_name = os.path.splitext(data['filename'])[0]
                fallback_url = FALLBACK_URL_TEMPLATE.format(seed=seed_name)
                try:
                    download_image(data['image_url'], dest, fallback_url=fallback_url)
                except Exception as e:
                    print(f"  Warning: could not download {data['filename']}: {e}")
                    continue

            item = ClothingItem(
                name=data['name'],
                category=data['category'],
                color_primary=data['color_primary'],
                style_tags=data['style_tags'],
                season=data['season'],
                photo_path=data['filename'],
            )
            db.session.add(item)

        db.session.commit()
        count = ClothingItem.query.count()
        print(f"Done. Seeded {count} clothing items.")


if __name__ == '__main__':
    seed()
