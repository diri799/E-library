import os

from flask import Blueprint, abort, current_app, jsonify, request, send_from_directory
from sqlalchemy import or_

from app import db
from models import Book, Category
from routes.auth import role_required


user_bp = Blueprint("user", __name__)


def _serialize_book(book):
    return {
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "category": book.category.name if book.category else None,
        "type": book.type,
        "file_url": book.file_url,
        "can_download": book.can_download,
        "created_at": book.created_at.isoformat(),
    }


def _send_upload_file(file_url, as_attachment=False, download_name=None, mimetype=None):
    filename = os.path.basename(file_url)
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    file_path = os.path.join(upload_folder, filename)
    if not os.path.exists(file_path):
        abort(404)
    return send_from_directory(
        upload_folder,
        filename,
        as_attachment=as_attachment,
        download_name=download_name,
        mimetype=mimetype,
    )


@user_bp.route("/books", methods=["GET"])
@role_required("admin", "user")
def view_books():
    query = db.session.query(Book).outerjoin(Category)
    search = (request.args.get("search") or "").strip()
    title = (request.args.get("title") or "").strip()
    author = (request.args.get("author") or "").strip()
    category = (request.args.get("category") or "").strip()

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Book.title.ilike(search_term),
                Book.author.ilike(search_term),
                Category.name.ilike(search_term),
            )
        )
    if title:
        query = query.filter(Book.title.ilike(f"%{title}%"))
    if author:
        query = query.filter(Book.author.ilike(f"%{author}%"))
    if category:
        query = query.filter(Category.name.ilike(f"%{category}%"))

    books = query.order_by(Book.created_at.desc()).all()
    return jsonify({"books": [_serialize_book(book) for book in books]}), 200


@user_bp.route("/books/<int:book_id>/read", methods=["GET"])
@role_required("admin", "user")
def read_book(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({"error": "book not found"}), 404
    if book.type != "book":
        return jsonify({"error": "this item is not a PDF book"}), 400

    download_name = f"{book.title}.pdf"
    return _send_upload_file(
        book.file_url,
        as_attachment=False,
        download_name=download_name,
        mimetype="application/pdf",
    )


@user_bp.route("/books/<int:book_id>/download", methods=["GET"])
@role_required("admin", "user")
def download_book(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({"error": "book not found"}), 404
    if book.type != "book":
        return jsonify({"error": "only PDF books can be downloaded"}), 400
    if not book.can_download:
        return jsonify({"error": "download not allowed for this book"}), 403

    download_name = f"{book.title}.pdf"
    return _send_upload_file(
        book.file_url,
        as_attachment=True,
        download_name=download_name,
        mimetype="application/pdf",
    )


@user_bp.route("/videos/<int:book_id>/watch", methods=["GET"])
@role_required("admin", "user")
def watch_video(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({"error": "video not found"}), 404
    if book.type != "video":
        return jsonify({"error": "this item is not a video"}), 400

    download_name = f"{book.title}.mp4"
    return _send_upload_file(
        book.file_url,
        as_attachment=False,
        download_name=download_name,
        mimetype="video/mp4",
    )
