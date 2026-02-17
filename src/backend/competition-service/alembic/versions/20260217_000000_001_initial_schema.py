"""Initial schema for A.V.A.R Competition Service

Revision ID: 001
Revises:
Create Date: 2026-02-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all initial tables"""

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('bio', sa.String(length=1000), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('role', sa.Enum('PARTICIPANT', 'JUDGE', 'ORGANIZER', 'ADMIN', name='userrole'),
                  nullable=False, server_default='PARTICIPANT'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_id', 'users', ['id'], unique=False)

    # Create competitions table
    op.create_table(
        'competitions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('rules', sa.Text(), nullable=True),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('submission_start', sa.DateTime(), nullable=False),
        sa.Column('submission_end', sa.DateTime(), nullable=False),
        sa.Column('judging_start', sa.DateTime(), nullable=True),
        sa.Column('judging_end', sa.DateTime(), nullable=True),
        sa.Column('results_date', sa.DateTime(), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'OPEN', 'CLOSED', 'JUDGING', 'COMPLETED', 'CANCELLED',
                  name='competitionstatus'), nullable=False, server_default='DRAFT'),
        sa.Column('max_submissions_per_user', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('require_raw_files', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('allow_ai_generated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('entry_fee', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('banner_url', sa.String(length=500), nullable=True),
        sa.Column('thumbnail_url', sa.String(length=500), nullable=True),
        sa.Column('prize_description', sa.Text(), nullable=True),
        sa.Column('prize_amount', sa.Integer(), nullable=True),
        sa.Column('organizer_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['organizer_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_competitions_title', 'competitions', ['title'], unique=False)
    op.create_index('ix_competitions_slug', 'competitions', ['slug'], unique=True)
    op.create_index('ix_competitions_id', 'competitions', ['id'], unique=False)

    # Create submissions table
    op.create_table(
        'submissions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('jpg_file_url', sa.String(length=500), nullable=False),
        sa.Column('jpg_file_size', sa.Integer(), nullable=False),
        sa.Column('raw_file_url', sa.String(length=500), nullable=True),
        sa.Column('raw_file_size', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'ANALYZING', 'APPROVED', 'REJECTED', 'DISQUALIFIED',
                  name='submissionstatus'), nullable=False, server_default='PENDING'),
        sa.Column('verification_verdict', sa.Enum('AUTHENTIC', 'SUSPICIOUS', 'AI_GENERATED', 'NEEDS_REVIEW',
                  name='verificationverdict'), nullable=True),
        sa.Column('verification_confidence', sa.Float(), nullable=True),
        sa.Column('verification_details', sa.JSON(), nullable=True),
        sa.Column('verification_timestamp', sa.String(length=50), nullable=True),
        sa.Column('camera_make', sa.String(length=100), nullable=True),
        sa.Column('camera_model', sa.String(length=100), nullable=True),
        sa.Column('lens_model', sa.String(length=100), nullable=True),
        sa.Column('iso', sa.Integer(), nullable=True),
        sa.Column('aperture', sa.String(length=20), nullable=True),
        sa.Column('shutter_speed', sa.String(length=20), nullable=True),
        sa.Column('capture_date', sa.String(length=50), nullable=True),
        sa.Column('total_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('score_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('competition_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['competition_id'], ['competitions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_submissions_id', 'submissions', ['id'], unique=False)
    op.create_index('ix_submissions_user_id', 'submissions', ['user_id'], unique=False)
    op.create_index('ix_submissions_competition_id', 'submissions', ['competition_id'], unique=False)

    # Create judges table
    op.create_table(
        'judges',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('specialization', sa.String(length=255), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index('ix_judges_id', 'judges', ['id'], unique=False)

    # Create judge_assignments table
    op.create_table(
        'judge_assignments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('judge_id', sa.Integer(), nullable=False),
        sa.Column('competition_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['judge_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['competition_id'], ['competitions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_judge_assignments_id', 'judge_assignments', ['id'], unique=False)
    op.create_index('ix_judge_assignments_judge_competition', 'judge_assignments',
                    ['judge_id', 'competition_id'], unique=True)

    # Create scores table
    op.create_table(
        'scores',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('composition_score', sa.Float(), nullable=False),
        sa.Column('technical_score', sa.Float(), nullable=False),
        sa.Column('creativity_score', sa.Float(), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('submission_id', sa.Integer(), nullable=False),
        sa.Column('judge_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['submission_id'], ['submissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['judge_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_scores_id', 'scores', ['id'], unique=False)
    op.create_index('ix_scores_submission_judge', 'scores',
                    ['submission_id', 'judge_id'], unique=True)


def downgrade() -> None:
    """Drop all tables in reverse order"""
    op.drop_index('ix_scores_submission_judge', 'scores')
    op.drop_index('ix_scores_id', 'scores')
    op.drop_table('scores')

    op.drop_index('ix_judge_assignments_judge_competition', 'judge_assignments')
    op.drop_index('ix_judge_assignments_id', 'judge_assignments')
    op.drop_table('judge_assignments')

    op.drop_index('ix_judges_id', 'judges')
    op.drop_table('judges')

    op.drop_index('ix_submissions_competition_id', 'submissions')
    op.drop_index('ix_submissions_user_id', 'submissions')
    op.drop_index('ix_submissions_id', 'submissions')
    op.drop_table('submissions')

    op.drop_index('ix_competitions_id', 'competitions')
    op.drop_index('ix_competitions_slug', 'competitions')
    op.drop_index('ix_competitions_title', 'competitions')
    op.drop_table('competitions')

    op.drop_index('ix_users_id', 'users')
    op.drop_index('ix_users_username', 'users')
    op.drop_index('ix_users_email', 'users')
    op.drop_table('users')

    # Drop enum types
    sa.Enum(name='verificationverdict').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='submissionstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='competitionstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='userrole').drop(op.get_bind(), checkfirst=True)
