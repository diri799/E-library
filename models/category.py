from datetime import datetime, UTC

from app import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))

    books = db.relationship(
        "Book",
        back_populates="category",
        cascade="all, delete-orphan",
        lazy=True,
    )
