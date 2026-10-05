"""add tsvector trigger and index

Revision ID: daa28468fddd
Revises: d930a969c4f9
Create Date: 2026-10-05 09:33:10.871450

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "daa28468fddd"
down_revision: str | Sequence[str] | None = "d930a969c4f9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
        CREATE INDEX ix_content_lessons_search_vector ON content.lessons USING GIN (search_vector);
        
        CREATE FUNCTION content.lessons_search_vector_trigger() RETURNS trigger AS $$
        begin
            new.search_vector :=
                setweight(to_tsvector('pg_catalog.english', coalesce(new.title, '')), 'A') ||
                setweight(to_tsvector('pg_catalog.english', coalesce(new.body, '')), 'B');
            return new;
        end
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER tsvectorupdate
        BEFORE INSERT OR UPDATE
        ON content.lessons
        FOR EACH ROW EXECUTE FUNCTION content.lessons_search_vector_trigger();

        ALTER TABLE content.categories ADD COLUMN search_vector tsvector;
        CREATE INDEX ix_content_categories_search_vector 
        ON content.categories USING GIN (search_vector);

        CREATE FUNCTION content.categories_search_vector_trigger() RETURNS trigger AS $$
        begin
            new.search_vector :=
                setweight(to_tsvector('pg_catalog.english', coalesce(new.name, '')), 'A');
            return new;
        end
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER tsvectorupdate_categories
        BEFORE INSERT OR UPDATE
        ON content.categories
        FOR EACH ROW EXECUTE FUNCTION content.categories_search_vector_trigger();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("""
        DROP TRIGGER IF EXISTS tsvectorupdate_categories ON content.categories;
        DROP FUNCTION IF EXISTS content.categories_search_vector_trigger();
        DROP INDEX IF EXISTS content.ix_content_categories_search_vector;
        ALTER TABLE content.categories DROP COLUMN IF EXISTS search_vector;

        DROP TRIGGER IF EXISTS tsvectorupdate ON content.lessons;
        DROP FUNCTION IF EXISTS content.lessons_search_vector_trigger();
        DROP INDEX IF EXISTS content.ix_content_lessons_search_vector;
    """)
