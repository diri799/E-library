import os

from flask import Flask, render_template
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6"
)
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", app.config["SECRET_KEY"])

database_url = os.environ.get("DATABASE_URL")
if database_url:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'library.db')}"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
upload_folder = os.environ.get("UPLOAD_FOLDER", "uploads")
if not os.path.isabs(upload_folder):
    upload_folder = os.path.join(BASE_DIR, upload_folder)
app.config["UPLOAD_FOLDER"] = upload_folder

raw_cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173")
cors_origins = [origin.strip() for origin in raw_cors_origins.split(",") if origin.strip()]
CORS(app, resources={r"/*": {"origins": cors_origins}})

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
jwt = JWTManager(app)

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

from models import AdminRequest, Book, Category, User
from routes import admin_bp, auth_bp, user_bp
from routes.admin import (
    approve_admin_request as approve_admin_request_handler,
    create_admin as create_admin_handler,
    deny_admin_request as deny_admin_request_handler,
    get_admin_requests as get_admin_requests_handler,
)


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


def ensure_bootstrap_admin():
    """Create a permanent fallback admin account if it doesn't exist."""
    admin_email = "admin@elibrary.local"
    admin_password = "Admin@12345"
    admin_name = "System Admin"

    existing_admin = User.query.filter_by(email=admin_email).first()
    if existing_admin:
        return

    admin_user = User(
        name=admin_name,
        email=admin_email,
        role="admin",
        is_active=True,
        created_by=None,
    )
    admin_user.set_password(admin_password)
    db.session.add(admin_user)
    db.session.commit()


app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(user_bp)
app.add_url_rule(
    "/api/admin/create-admin",
    view_func=create_admin_handler,
    methods=["POST"],
    endpoint="api_create_admin",
)
app.add_url_rule(
    "/api/admin/admin-requests",
    view_func=get_admin_requests_handler,
    methods=["GET"],
    endpoint="api_get_admin_requests",
)
app.add_url_rule(
    "/api/admin/admin-requests/<int:request_id>/approve",
    view_func=approve_admin_request_handler,
    methods=["PATCH"],
    endpoint="api_approve_admin_request",
)
app.add_url_rule(
    "/api/admin/admin-requests/<int:request_id>/deny",
    view_func=deny_admin_request_handler,
    methods=["PATCH"],
    endpoint="api_deny_admin_request",
)

with app.app_context():
    db.create_all()
    ensure_bootstrap_admin()


@app.route("/")
def index():
    return render_template("index.html")


@app.errorhandler(404)
def not_found_error(_error):
    return {"error": "Resource not found"}, 404


@app.errorhandler(500)
def internal_server_error(_error):
    return {"error": "Internal server error"}, 500



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)