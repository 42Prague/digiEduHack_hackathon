"""Add transcripts and cultural_analysis tables

Revision ID: add_transcripts_cultural
Revises: a9f3e8a0776f
Create Date: 2025-11-13 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_transcripts_cultural"
down_revision = "a9f3e8a0776f"
branch_labels = None
depends_on = None


def upgrade():
    """Apply migration changes."""
    # Create transcripts table
    op.create_table(
        'transcripts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('original_filename', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column('file_paths', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('upload_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('transcript_text', sa.Text(), nullable=True),
        sa.Column('clean_text', sa.Text(), nullable=True),
        sa.Column('raw_file_path', sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=True),
        sa.Column('transcript_path', sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transcripts_id'), 'transcripts', ['id'], unique=False)
    
    # Create cultural_analysis table
    op.create_table(
        'cultural_analysis',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transcript_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mindset_shift_score', sa.Integer(), nullable=False),
        sa.Column('collaboration_score', sa.Integer(), nullable=False),
        sa.Column('teacher_confidence_score', sa.Integer(), nullable=False),
        sa.Column('municipality_cooperation_score', sa.Integer(), nullable=False),
        sa.Column('sentiment_score', sa.Integer(), nullable=False),
        sa.Column('themes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('practical_change', sa.Text(), nullable=True),
        sa.Column('mindset_change', sa.Text(), nullable=True),
        sa.Column('impact_summary', sa.Text(), nullable=True),
        sa.Column('culture_change_detected', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['transcript_id'], ['transcripts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cultural_analysis_id'), 'cultural_analysis', ['id'], unique=False)
    op.create_index(op.f('ix_cultural_analysis_transcript_id'), 'cultural_analysis', ['transcript_id'], unique=False)


def downgrade():
    """Rollback migration changes."""
    op.drop_index(op.f('ix_cultural_analysis_transcript_id'), table_name='cultural_analysis')
    op.drop_index(op.f('ix_cultural_analysis_id'), table_name='cultural_analysis')
    op.drop_table('cultural_analysis')
    op.drop_index(op.f('ix_transcripts_id'), table_name='transcripts')
    op.drop_table('transcripts')

