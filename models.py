from datetime import datetime
import json
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class ClothingItem(db.Model):
    __tablename__ = 'clothing_items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(20), nullable=False)
    color_primary = db.Column(db.String(30), nullable=False)
    color_secondary = db.Column(db.String(30), nullable=True)
    style_tags = db.Column(db.String(100), nullable=False)
    season = db.Column(db.String(20), nullable=False, default='all')
    photo_path = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'color_primary': self.color_primary,
            'color_secondary': self.color_secondary,
            'style_tags': [t.strip() for t in self.style_tags.split(',') if t.strip()],
            'season': self.season,
            'photo_path': self.photo_path,
            'created_at': self.created_at.isoformat(),
        }


class Outfit(db.Model):
    __tablename__ = 'outfits'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)
    item_ids = db.Column(db.String(200), nullable=False)
    score = db.Column(db.Float, nullable=False)
    occasion = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'item_ids': json.loads(self.item_ids),
            'score': self.score,
            'occasion': self.occasion,
            'created_at': self.created_at.isoformat(),
        }
