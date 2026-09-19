# Reorganized web layer

The Flask application now serves pages from `web/templates/` and assets from `web/static/`.

The original front-end files remain temporarily at the repository root for backwards compatibility while the new structure is validated. New links should use the Flask routes and `url_for`.
