from app import app, db
from models import Product

with app.app_context():
    db.create_all()