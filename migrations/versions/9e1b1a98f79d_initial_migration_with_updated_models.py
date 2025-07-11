"""Initial migration with updated models

Revision ID: 9e1b1a98f79d
Revises: 
Create Date: 2025-06-06 14:22:39.900023

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9e1b1a98f79d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('policy_chunks',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('policy_id', sa.String(length=100), nullable=False),
    sa.Column('document_source_filename', sa.String(length=512), nullable=True),
    sa.Column('section_type', sa.String(length=100), nullable=True),
    sa.Column('chunk_text', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('policy_chunks', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_policy_chunks_policy_id'), ['policy_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_policy_chunks_section_type'), ['section_type'], unique=False)

    op.create_table('processed_policy_data',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('original_document_gcs_path', sa.String(length=512), nullable=False),
    sa.Column('processed_json_gcs_path', sa.String(length=512), nullable=False),
    sa.Column('policy_number', sa.String(length=100), nullable=True),
    sa.Column('insurer_name', sa.String(length=255), nullable=True),
    sa.Column('policyholder_name', sa.String(length=255), nullable=True),
    sa.Column('property_address', sa.String(length=512), nullable=True),
    sa.Column('effective_date', sa.Date(), nullable=True),
    sa.Column('expiration_date', sa.Date(), nullable=True),
    sa.Column('total_premium', sa.Float(), nullable=True),
    sa.Column('coverage_details', sa.JSON(), nullable=True),
    sa.Column('raw_text', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('processed_policy_data', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_processed_policy_data_policy_number'), ['policy_number'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('processed_policy_data', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_processed_policy_data_policy_number'))

    op.drop_table('processed_policy_data')
    with op.batch_alter_table('policy_chunks', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_policy_chunks_section_type'))
        batch_op.drop_index(batch_op.f('ix_policy_chunks_policy_id'))

    op.drop_table('policy_chunks')
    # ### end Alembic commands ###
