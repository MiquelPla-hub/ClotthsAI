import os
import uuid
import json
from flask import Flask, request, jsonify, send_from_directory, abort
from werkzeug.utils import secure_filename
from models import db, ClothingItem, Outfit
from recommender import generate_suggestions


def create_app(config=None):
    app = Flask(__name__, static_folder='static', static_url_path='')
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "wardrobe.db")}'
    app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'uploads')
    if config:
        app.config.update(config)
    db.init_app(app)

    _OUTFIT_REGEN_LIMIT = 9999

    def regenerate_outfits():
        try:
            Outfit.query.delete()
            items = ClothingItem.query.all()
            suggestions = generate_suggestions(items, style_filter='all', limit=_OUTFIT_REGEN_LIMIT)
            for s in suggestions:
                db.session.add(Outfit(
                    item_ids=json.dumps([i['id'] for i in s['items']]),
                    score=s['score'],
                    occasion=s['occasion'],
                ))
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    @app.route('/')
    def index():
        return send_from_directory('static', 'index.html')

    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    @app.route('/api/clothes', methods=['GET'])
    def get_clothes():
        q = ClothingItem.query
        if category := request.args.get('category'):
            q = q.filter_by(category=category)
        if season := request.args.get('season'):
            q = q.filter(ClothingItem.season.in_([season, 'all']))
        if style := request.args.get('style'):
            q = q.filter(ClothingItem.style_tags.contains(style))

        all_outfits = Outfit.query.all()
        outfit_id_sets = [set(json.loads(o.item_ids)) for o in all_outfits]

        result = []
        for item in q.all():
            d = item.to_dict()
            d['outfit_count'] = sum(1 for ids in outfit_id_sets if item.id in ids)
            result.append(d)
        return jsonify(result)

    @app.route('/api/clothes', methods=['POST'])
    def add_clothes():
        name = request.form.get('name')
        category = request.form.get('category')
        color_primary = request.form.get('color_primary')
        style_tags = request.form.get('style_tags')

        if not all([name, category, color_primary, style_tags]):
            return jsonify({'error': 'Missing required fields'}), 400

        photo = request.files.get('photo')
        if not photo:
            return jsonify({'error': 'Photo is required'}), 400

        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        safe_name = secure_filename(photo.filename) or 'upload'
        filename = f"{uuid.uuid4().hex}_{safe_name}"
        photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        item = ClothingItem(
            name=name,
            category=category,
            color_primary=color_primary,
            color_secondary=request.form.get('color_secondary') or None,
            style_tags=style_tags,
            season=request.form.get('season', 'all'),
            photo_path=filename,
        )
        db.session.add(item)
        db.session.commit()
        regenerate_outfits()
        return jsonify(item.to_dict()), 201

    @app.route('/api/clothes/<int:item_id>', methods=['DELETE'])
    def delete_clothes(item_id):
        item = db.session.get(ClothingItem, item_id)
        if item is None:
            abort(404)
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], item.photo_path)
        if os.path.exists(photo_path):
            os.remove(photo_path)
        db.session.delete(item)
        db.session.commit()
        regenerate_outfits()
        return jsonify({'deleted': item_id})

    @app.route('/api/outfits', methods=['GET'])
    def get_outfits():
        item_id = request.args.get('item_id', type=int)
        all_outfits = Outfit.query.order_by(Outfit.score.desc()).all()
        result = []
        for o in all_outfits:
            ids = json.loads(o.item_ids)
            if item_id is not None and item_id not in ids:
                continue
            items = [db.session.get(ClothingItem, i) for i in ids]
            items = [i for i in items if i]
            result.append({
                'id': o.id,
                'score': o.score,
                'occasion': o.occasion,
                'items': [i.to_dict() for i in items],
            })
        return jsonify(result)

    @app.route('/api/suggest', methods=['GET'])
    def suggest_outfits():
        style = request.args.get('style', 'all')
        try:
            limit = max(1, int(request.args.get('limit', 20)))
        except (ValueError, TypeError):
            return jsonify({'error': 'limit must be a positive integer'}), 400
        items = ClothingItem.query.all()
        suggestions = generate_suggestions(items, style_filter=style, limit=limit)
        return jsonify(suggestions)

    return app


app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, port=5000)
