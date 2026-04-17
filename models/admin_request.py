from datetime import datetime, UTC

from app import db


class AdminRequest(db.Model):
    __tablename__ = "admin_requests"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="pending", index=True)
    deny_reason = db.Column(db.String(500), nullable=True)
    requested_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    __table_args__ = (
        db.CheckConstraint("status IN ('pending', 'approved', 'denied')", name="check_admin_request_status"),
    )
