from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)

# Configure the database URI with your ElephantSQL credentials
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://username:password@hostname:port/database_name'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Define the models
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    tags = db.relationship('Tag', backref='item', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Item {self.name}>'

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)

    def __repr__(self):
        return f'<Tag {self.name}>'

# Create the tables
with app.app_context():
    db.create_all()

# Define routes
@app.route('/items', methods=['GET', 'POST'])
def items():
    if request.method == 'GET':
        items = Item.query.all()
        result = [{'id': item.id, 'name': item.name, 'description': item.description, 'tags': [{'id': tag.id, 'name': tag.name} for tag in item.tags]} for item in items]
        return jsonify(result)
    elif request.method == 'POST':
        data = request.json
        new_item = Item(name=data['name'], description=data['description'])
        db.session.add(new_item)
        db.session.commit()
        for tag_name in data.get('tags', []):
            new_tag = Tag(name=tag_name, item_id=new_item.id)
            db.session.add(new_tag)
        db.session.commit()
        return jsonify({'message': 'Item created successfully'}), 201

@app.route('/items/<int:item_id>', methods=['GET', 'PUT', 'DELETE'])
def single_item(item_id):
    item = Item.query.get_or_404(item_id)
    if request.method == 'GET':
        return jsonify({'id': item.id, 'name': item.name, 'description': item.description, 'tags': [{'id': tag.id, 'name': tag.name} for tag in item.tags]})
    elif request.method == 'PUT':
        data = request.json
        item.name = data.get('name', item.name)
        item.description = data.get('description', item.description)
        db.session.commit()
        existing_tag_ids = [tag.id for tag in item.tags]
        new_tag_ids = []
        for tag_data in data.get('tags', []):
            tag = Tag.query.get(tag_data['id'])
            if tag:
                tag.name = tag_data['name']
                new_tag_ids.append(tag.id)
            else:
                new_tag = Tag(name=tag_data['name'], item_id=item.id)
                db.session.add(new_tag)
                db.session.commit()
                new_tag_ids.append(new_tag.id)
        for tag_id in set(existing_tag_ids) - set(new_tag_ids):
            Tag.query.filter_by(id=tag_id).delete()
        db.session.commit()
        return jsonify({'message': 'Item updated successfully'})
    elif request.method == 'DELETE':
        db.session.delete(item)
        db.session.commit()
        return jsonify({'message': 'Item deleted successfully'})

@app.route('/tags', methods=['GET'])
def get_tags():
    tags = Tag.query.all()
    result = [{'id': tag.id, 'name': tag.name, 'item_id': tag.item_id} for tag in tags]
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
