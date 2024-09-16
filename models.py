from database import db
from flask_login import UserMixin
from flask_wtf import CSRFProtect
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    picture = db.Column(db.String(120), nullable=True)
    title = db.Column(db.String(150), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    isbn = db.Column(db.String(20), unique=True, nullable=False)
    genre = db.Column(db.String(50), nullable=True)
    description = db.Column(db.String(50), nullable=False)
    publication_year = db.Column(db.Integer)
    available_quantity = db.Column(db.Integer, default=1)
    total_quantity = db.Column(db.Integer, default=1)
    shelf = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Book {self.title}>'

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    borrow_history = db.relationship('Loan', backref='member', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Admin {self.username}>'

class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    borrow_date = db.Column(db.DateTime, default=datetime.utcnow)
    return_date = db.Column(db.DateTime, nullable=True)
    due_date = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(days=14))
    status = db.Column(db.String(50), default='borrowed')  # Options: 'borrowed', 'returned', 'overdue'
    book = db.relationship('Book', backref=db.backref('loans', lazy=True))

    def __repr__(self):
        return f'<Loan Book ID: {self.book_id}, Member ID: {self.member_id}>'
    
class Ebook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)