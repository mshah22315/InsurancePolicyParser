"""add cosine similarity function

Revision ID: add_cosine_similarity
Revises: 49c55d02b1f4
Create Date: 2024-03-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_cosine_similarity'
down_revision = '49c55d02b1f4'
branch_labels = None
depends_on = None

def upgrade():
    # Create the cosine_similarity function
    op.execute("""
    CREATE OR REPLACE FUNCTION cosine_similarity(a double precision[], b double precision[])
    RETURNS double precision
    LANGUAGE plpgsql
    AS $$
    DECLARE
        dot_product double precision;
        norm_a double precision;
        norm_b double precision;
        epsilon double precision := 1e-10;  -- Small value to prevent division by zero
    BEGIN
        -- Calculate dot product
        SELECT sum(a[i] * b[i])
        INTO dot_product
        FROM generate_series(1, array_length(a, 1)) AS i;
        
        -- Calculate L2 norm of a
        SELECT sqrt(sum(a[i] * a[i]))
        INTO norm_a
        FROM generate_series(1, array_length(a, 1)) AS i;
        
        -- Calculate L2 norm of b
        SELECT sqrt(sum(b[i] * b[i]))
        INTO norm_b
        FROM generate_series(1, array_length(b, 1)) AS i;
        
        -- Handle zero vectors
        IF norm_a < epsilon OR norm_b < epsilon THEN
            RETURN 0;
        END IF;
        
        -- Return cosine similarity
        RETURN dot_product / (norm_a * norm_b);
    END;
    $$;
    """)

def downgrade():
    # Drop the cosine_similarity function
    op.execute("DROP FUNCTION IF EXISTS cosine_similarity(double precision[], double precision[]);") 