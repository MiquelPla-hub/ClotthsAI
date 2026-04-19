import pytest
import json
from app import create_app
from models import db, ClothingItem, Outfit


@pytest.fixture
def app(tmp_path):
    flask_app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'UPLOAD_FOLDER': str(tmp_path),
    })
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.drop_all()


def test_clothing_item_creation(app):
    with app.app_context():
        item = ClothingItem(
            name='White Oxford',
            category='top',
            color_primary='white',
            style_tags='smart-casual',
            season='all',
            photo_path='test.jpg',
        )
        db.session.add(item)
        db.session.commit()
        assert item.id is not None
        assert item.name == 'White Oxford'


def test_clothing_item_to_dict(app):
    with app.app_context():
        item = ClothingItem(
            name='Black Jeans',
            category='bottom',
            color_primary='black',
            style_tags='casual',
            season='all',
            photo_path='jeans.jpg',
        )
        db.session.add(item)
        db.session.commit()
        d = item.to_dict()
        assert d['name'] == 'Black Jeans'
        assert d['style_tags'] == ['casual']
        assert 'id' in d
        assert 'created_at' in d


def test_outfit_creation(app):
    with app.app_context():
        outfit = Outfit(
            item_ids=json.dumps([1, 2, 3]),
            score=0.87,
            occasion='casual',
        )
        db.session.add(outfit)
        db.session.commit()
        assert outfit.id is not None


def test_outfit_to_dict(app):
    with app.app_context():
        outfit = Outfit(
            name='My Outfit',
            item_ids=json.dumps([1, 2, 3]),
            score=0.92,
            occasion='smart-casual',
        )
        db.session.add(outfit)
        db.session.commit()
        d = outfit.to_dict()
        assert d['item_ids'] == [1, 2, 3]
        assert d['score'] == 0.92
        assert d['name'] == 'My Outfit'
