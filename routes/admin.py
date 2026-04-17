import os
from uuid import uuid4

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename

from app import db
from models import Book, Category, User
from routes.auth import role_required


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

BOOK_EXTENSIONS = {"pdf"}
VIDEO_EXTENSIONS = {"mp4"}


def _parse_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y", "on"}


def _save_uploaded_file(file_storage, content_type):
    filename = secure_filename(file_storage.filename or "")
    if not filename:
        raise ValueError("file is required")

    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if content_type == "book" and extension not in BOOK_EXTENSIONS:
        raise ValueError("books must be uploaded as PDF files")
    if content_type == "video" and extension not in VIDEO_EXTENSIONS:
        raise ValueError("videos must be uploaded as MP4 files")

    stored_name = f"{uuid4().hex}_{filename}"
    upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], stored_name)
    file_storage.save(upload_path)
    file_url = f"/uploads/{stored_name}"
    return file_url


@admin_bp.route("/categories", methods=["POST"])
@role_required("admin")
def add_category():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    existing = Category.query.filter_by(name=name).first()
    if existing:
        return jsonify({"error": "category already exists"}), 409

    category = Category(name=name)
    db.session.add(category)
    db.session.commit()
    return jsonify({"id": category.id, "name": category.name}), 201


@admin_bp.route("/categories", methods=["GET"])
@role_required("admin")
def view_categories():
    categories = Category.query.order_by(Category.name.asc()).all()
    data = [{"id": category.id, "name": category.name} for category in categories]
    return jsonify({"categories": data}), 200


@admin_bp.route("/categories/<int:category_id>", methods=["DELETE"])
@role_required("admin")
def delete_category(category_id):
    category = Category.query.get(category_id)
    if not category:
        return jsonify({"error": "category not found"}), 404

    db.session.delete(category)
    db.session.commit()
    return jsonify({"message": "category deleted"}), 200


@admin_bp.route("/books", methods=["POST"])
@role_required("admin")
def add_book():
    form = request.form
    title = (form.get("title") or "").strip()
    author = (form.get("author") or "").strip()
    content_type = (form.get("type") or "").strip().lower()
    category_id = form.get("category_id")
    can_download = _parse_bool(form.get("can_download"), default=False)
    uploaded_file = request.files.get("file")

    if not title or not author or not category_id or not content_type or not uploaded_file:
        return (
            jsonify({"error": "title, author, type, category_id, and file are required"}),
            400,
        )
    if content_type not in {"book", "video"}:
        return jsonify({"error": "type must be either book or video"}), 400

    category = db.session.get(Category, category_id)
    if not category:
        return jsonify({"error": "category not found"}), 404

    try:
        file_url = _save_uploaded_file(uploaded_file, content_type)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    book = Book(
        title=title,
        author=author,
        category_id=category.id,
        type=content_type,
        file_url=file_url,
        can_download=can_download,
    )
    db.session.add(book)
    db.session.commit()

    return (
        jsonify(
            {
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "type": book.type,
                "file_url": book.file_url,
                "can_download": book.can_download,
                "category_id": book.category_id,
            }
        ),
        201,
    )


@admin_bp.route("/books/<int:book_id>", methods=["PUT"])
@role_required("admin")
def edit_book(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({"error": "book not found"}), 404

    form = request.form
    requested_type = (form.get("type") or "").strip().lower()
    if requested_type and requested_type not in {"book", "video"}:
        return jsonify({"error": "type must be either book or video"}), 400

    if form.get("title"):
        book.title = form.get("title").strip()
    if form.get("author"):
        book.author = form.get("author").strip()
    if form.get("category_id"):
        category = db.session.get(Category, form.get("category_id"))
        if not category:
            return jsonify({"error": "category not found"}), 404
        book.category_id = category.id
    if requested_type:
        book.type = requested_type
    if form.get("can_download") is not None:
        book.can_download = _parse_bool(form.get("can_download"), default=book.can_download)

    uploaded_file = request.files.get("file")
    if uploaded_file:
        target_type = requested_type or book.type
        try:
            file_url = _save_uploaded_file(uploaded_file, target_type)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        old_path = os.path.join(current_app.root_path, book.file_url.lstrip("/"))
        if os.path.exists(old_path):
            os.remove(old_path)
        book.file_url = file_url

    db.session.commit()
    return jsonify({"message": "book updated"}), 200


@admin_bp.route("/books/<int:book_id>", methods=["DELETE"])
@role_required("admin")
def delete_book(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({"error": "book not found"}), 404

    file_path = os.path.join(current_app.root_path, book.file_url.lstrip("/"))
    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(book)
    db.session.commit()
    return jsonify({"message": "book deleted"}), 200


@admin_bp.route("/dashboard", methods=["GET"])
@role_required("admin")
def dashboard():
    return (
        jsonify(
            {
                "users_count": User.query.count(),
                "books_count": Book.query.count(),
                "categories_count": Category.query.count(),
            }
        ),
        200,
    )


@admin_bp.route("/create-admin", methods=["POST"])
@role_required("admin")
def create_admin():
    from flask_jwt_extended import get_jwt_identity

    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""

    if not name or not email or not password:
        return jsonify({"error": "name, email, and password are required"}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "email is already registered"}), 409

    creator_id = get_jwt_identity()
    try:
        creator_id = int(creator_id)
    except (TypeError, ValueError):
        return jsonify({"error": "invalid admin identity"}), 401

    new_admin = User(
        name=name,
        email=email,
        role="admin",
        is_active=True,
        created_by=creator_id,
    )
    new_admin.set_password(password)
    db.session.add(new_admin)
    db.session.commit()

    return (
        jsonify(
            {
                "message": "admin created successfully",
                "user": {
                    "id": new_admin.id,
                    "name": new_admin.name,
                    "email": new_admin.email,
                    "role": new_admin.role,
                    "is_active": new_admin.is_active,
                    "created_by": new_admin.created_by,
                },
            }
        ),
        201,
    )
