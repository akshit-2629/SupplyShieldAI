"""
Phase 3 database setup — creates the news_articles table.

This script is safe to run multiple times (uses CREATE TABLE IF NOT EXISTS).
Run from the backend/ directory:
  python -m app.db.migrations.setup_phase3
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

def create_tables():
    from app.db.session import engine
    from app.db.models.base import Base
    # Import all models so SQLAlchemy knows about them
    import app.db.base  # noqa: F401 — triggers all model imports
    
    print("Creating Phase 3 tables (news_articles)...")
    try:
        Base.metadata.create_all(bind=engine, checkfirst=True)
        print("✓ Tables created successfully")
    except Exception as e:
        print(f"✗ Table creation failed: {e}")
        print("\nIf using Supabase, run the SQL file manually:")
        print("  backend/app/db/migrations/phase3_news_articles.sql")
        return False
    return True


if __name__ == "__main__":
    success = create_tables()
    sys.exit(0 if success else 1)
