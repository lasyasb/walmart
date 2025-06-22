from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class User(db.Model):
    """User model for storing account information and preferences"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    firebase_uid = db.Column(db.String(128), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    budgets = db.relationship('Budget', backref='user', lazy=True, cascade='all, delete-orphan')
    cart_items = db.relationship('CartItem', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.email}>'

class Budget(db.Model):
    """User budget settings"""
    __tablename__ = 'budgets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    month = db.Column(db.Integer, nullable=False)  # 1-12
    year = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint for one budget per user per month/year
    __table_args__ = (db.UniqueConstraint('user_id', 'month', 'year', name='unique_user_month_budget'),)
    
    def __repr__(self):
        return f'<Budget {self.amount} for {self.month}/{self.year}>'

class Product(db.Model):
    """Product catalog"""
    __tablename__ = 'products'
    
    id = db.Column(db.String(50), primary_key=True)  # Product ID from catalog
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    tags = db.Column(db.Text)  # JSON string of tags array
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    in_stock = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Product {self.name}>'

class CartItem(db.Model):
    """Personal cart items"""
    __tablename__ = 'cart_items'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.String(50), db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    product = db.relationship('Product', backref='cart_items')
    
    def __repr__(self):
        return f'<CartItem {self.product_id} x{self.quantity}>'

class SharedCartSession(db.Model):
    """Shared cart sessions with unique IDs"""
    __tablename__ = 'shared_cart_sessions'
    
    id = db.Column(db.String(8), primary_key=True)  # Short unique ID
    name = db.Column(db.String(100), nullable=False)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    created_by = db.relationship('User', backref='hosted_carts')
    items = db.relationship('SharedCartItem', backref='session', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<SharedCartSession {self.id}: {self.name}>'

class SharedCartItem(db.Model):
    """Items in shared cart sessions"""
    __tablename__ = 'shared_cart_items'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(8), db.ForeignKey('shared_cart_sessions.id'), nullable=False)
    product_id = db.Column(db.String(50), db.ForeignKey('products.id'), nullable=False)
    added_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    product = db.relationship('Product', backref='shared_cart_items')
    added_by = db.relationship('User', backref='shared_cart_contributions')
    
    def __repr__(self):
        return f'<SharedCartItem {self.product_id} in {self.session_id}>'

class RecommendationLog(db.Model):
    """Log of recommendation requests for analytics"""
    __tablename__ = 'recommendation_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    search_prompt = db.Column(db.String(255), nullable=False)
    budget_amount = db.Column(db.Numeric(10, 2))
    results_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='recommendation_logs')
    
    def __repr__(self):
        return f'<RecommendationLog "{self.search_prompt}" -> {self.results_count} results>'