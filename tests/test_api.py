import pytest
import io
from app import create_app
from models import db, ClothingItem


@pytest.fixture
def client(tmp_path):
    flask_app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'UPLOAD_FOLDER': str(tmp_path),
    })
    with flask_app.app_context():
        db.create_all()
        yield flask_app.test_client()
        db.drop_all()


def post_item(client, name='White Shirt', category='top', color='white', style='casual'):
    return client.post('/api/clothes', data={
        'name': name,
        'category': category,
        'color_primary': color,
        'style_tags': style,
        'season': 'all',
        'photo': (io.BytesIO(b'fake'), 'shirt.jpg'),
    }, content_type='multipart/form-data')


def test_get_clothes_empty(client):
    resp = client.get('/api/clothes')
    assert resp.status_code == 200
    assert resp.json == []


def test_add_clothes_returns_201(client):
    resp = post_item(client)
    assert resp.status_code == 201
    assert resp.json['name'] == 'White Shirt'
    assert resp.json['category'] == 'top'


def test_add_clothes_missing_fields_returns_400(client):
    resp = client.post('/api/clothes', data={
        'name': 'Shirt',
    }, content_type='multipart/form-data')
    assert resp.status_code == 400


def test_add_clothes_no_photo_returns_400(client):
    resp = client.post('/api/clothes', data={
        'name': 'Shirt',
        'category': 'top',
        'color_primary': 'white',
        'style_tags': 'casual',
    }, content_type='multipart/form-data')
    assert resp.status_code == 400


def test_get_clothes_returns_added_item(client):
    post_item(client)
    resp = client.get('/api/clothes')
    assert resp.status_code == 200
    assert len(resp.json) == 1
    assert resp.json[0]['name'] == 'White Shirt'


def test_get_clothes_filter_by_category(client):
    post_item(client, name='White Shirt', category='top')
    post_item(client, name='Black Jeans', category='bottom', color='black')
    resp = client.get('/api/clothes?category=top')
    assert len(resp.json) == 1
    assert resp.json[0]['category'] == 'top'


def test_delete_clothes(client):
    add_resp = post_item(client)
    item_id = add_resp.json['id']
    del_resp = client.delete(f'/api/clothes/{item_id}')
    assert del_resp.status_code == 200
    assert del_resp.json['deleted'] == item_id
    assert client.get('/api/clothes').json == []


def test_delete_nonexistent_item_returns_404(client):
    resp = client.delete('/api/clothes/99999')
    assert resp.status_code == 404


def test_suggest_empty_wardrobe(client):
    resp = client.get('/api/suggest')
    assert resp.status_code == 200
    assert resp.json == []


def test_suggest_with_complete_wardrobe(client):
    post_item(client, 'White Shirt', 'top', 'white', 'casual')
    post_item(client, 'Navy Chinos', 'bottom', 'navy', 'casual')
    post_item(client, 'White Sneakers', 'shoes', 'white', 'casual')
    resp = client.get('/api/suggest')
    assert resp.status_code == 200
    assert len(resp.json) == 1
    assert 'score' in resp.json[0]
    assert 'items' in resp.json[0]
    assert len(resp.json[0]['items']) == 3


def test_suggest_style_filter(client):
    post_item(client, 'White Shirt', 'top', 'white', 'casual')
    post_item(client, 'Navy Chinos', 'bottom', 'navy', 'casual')
    post_item(client, 'White Sneakers', 'shoes', 'white', 'casual')
    resp = client.get('/api/suggest?style=formal')
    assert resp.status_code == 200
    assert resp.json == []


def test_suggest_invalid_limit_returns_400(client):
    resp = client.get('/api/suggest?limit=abc')
    assert resp.status_code == 400


def test_get_outfits_empty(client):
    resp = client.get('/api/outfits')
    assert resp.status_code == 200
    assert resp.json == []
