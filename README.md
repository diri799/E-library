# E-library

## Deploy on Render

This project is ready for deployment on [Render](https://render.com/).

- **Build command:** `pip install -r requirements.txt`
- **Start command:** `gunicorn app:app`
- **Procfile:** `web: gunicorn app:app`

### Environment Variables

Set these in the Render dashboard:

- `SECRET_KEY` - Flask secret key
- `JWT_SECRET_KEY` - JWT signing key (can be different from `SECRET_KEY`)
- `DATABASE_URL` - Optional production database URL (recommended: PostgreSQL)
- `UPLOAD_FOLDER` - Optional upload directory path (defaults to `uploads`)
- `FLASK_DEBUG` - Set to `0` in production (default behavior)

### Database Notes

The app uses SQLite by default for local development. SQLite works for local/testing use, but it is not suitable for most production workloads. For production on Render, set `DATABASE_URL` to a PostgreSQL connection string.
