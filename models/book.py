from datetime import datetime, UTC

from app import db


class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(20), nullable=False, default="book")
    file_url = db.Column(db.String(500), nullable=False)
    can_download = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))

    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    category = db.relationship("Category", back_populates="books")

    __table_args__ = (
        db.CheckConstraint("type IN ('book', 'video')", name="check_book_type"),
    )
