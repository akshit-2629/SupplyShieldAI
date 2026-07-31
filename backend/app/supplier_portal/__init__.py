"""
supplier_portal/__init__.py — Phase 9 module entry point.
Import all models so Alembic discovers them for migration generation.
"""
import app.supplier_portal.models  # noqa: F401 — trigger model registration
