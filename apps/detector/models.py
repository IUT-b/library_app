from datetime import datetime

from apps.app import db


class UserBook(db.Model):
    __tablename__ = "user_books"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey("users.id"))
    title = db.Column(db.String)
    authors = db.Column(db.String)
    isbn = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class RecommendedBook(db.Model):
    __tablename__ = "recommended_books"
    id = db.Column(db.Integer, primary_key=True)
    media_id = db.Column(db.String)
    title = db.Column(db.String)
    authors = db.Column(db.String)
    link = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class UserLibrary(db.Model):
    __tablename__ = "user_libraries"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey("users.id"))
    systemid = db.Column(db.String)
    systemname = db.Column(db.String)
    libkey = db.Column(db.String)
    libid = db.Column(db.Integer)
    short = db.Column(db.String)
    formal = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
