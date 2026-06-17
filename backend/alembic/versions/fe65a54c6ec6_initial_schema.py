"""initial_schema

Revision ID: fe65a54c6ec6
Revises: 
Create Date: 2026-06-17 10:32:56.274343

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'fe65a54c6ec6'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema — full initial migration for SPEC-10."""

    # ── 1. Create independent tables first ───────────────────────────────
    op.create_table(
        'companies',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('subscription_plan', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('HR', 'TEAM_LEADER', name='userrole'), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )

    op.create_table(
        'teams',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('leader_id', sa.UUID(), nullable=True),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
        sa.ForeignKeyConstraint(['leader_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── 2. Upgrade meetings table BEFORE creating junction tables ─────────
    # meetings.id: VARCHAR → UUID  (must happen before FK references)
    op.execute("ALTER TABLE meetings ALTER COLUMN id TYPE UUID USING id::uuid")

    op.add_column('meetings', sa.Column('scheduled_time', sa.DateTime(timezone=True), nullable=True))
    op.add_column('meetings', sa.Column('company_id', sa.UUID(), nullable=True))   # nullable first
    op.add_column('meetings', sa.Column('created_by', sa.UUID(), nullable=True))

    op.alter_column('meetings', 'created_at',
                    existing_type=postgresql.TIMESTAMP(),
                    type_=sa.DateTime(timezone=True),
                    nullable=True)

    op.execute(
        "DO $$ BEGIN "
        "  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'meetingstatus') THEN "
        "    CREATE TYPE meetingstatus AS ENUM ("
        "      'PENDING','PROCESSING','JOINING','RECORDING',"
        "      'TRANSCRIBING','SUMMARISING','DELIVERING','COMPLETED','FAILED'"
        "    ); "
        "  END IF; "
        "END $$;"
    )
    op.execute(
        "ALTER TABLE meetings "
        "ALTER COLUMN status TYPE meetingstatus "
        "USING status::meetingstatus"
    )

    op.alter_column('meetings', 'error_message',
                    existing_type=sa.VARCHAR(),
                    type_=sa.Text(),
                    existing_nullable=True)
    op.alter_column('meetings', 'transcript',
                    existing_type=sa.VARCHAR(),
                    type_=sa.Text(),
                    existing_nullable=True)
    op.alter_column('meetings', 'summary',
                    existing_type=sa.VARCHAR(),
                    type_=sa.Text(),
                    existing_nullable=True)

    op.create_index(op.f('ix_meetings_session_id'), 'meetings', ['session_id'], unique=False)
    op.create_foreign_key('fk_meetings_created_by', 'meetings', 'users', ['created_by'], ['id'])
    op.create_foreign_key('fk_meetings_company_id', 'meetings', 'companies', ['company_id'], ['id'])

    # ── 3. Create junction tables (meetings.id is now UUID) ───────────────
    op.create_table(
        'members',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('team_id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'meeting_teams',
        sa.Column('meeting_id', sa.UUID(), nullable=False),
        sa.Column('team_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['meeting_id'], ['meetings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('meeting_id', 'team_id'),
    )

    op.create_table(
        'meeting_participants',
        sa.Column('meeting_id', sa.UUID(), nullable=False),
        sa.Column('member_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['meeting_id'], ['meetings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('meeting_id', 'member_id'),
    )


def downgrade() -> None:
    """Downgrade schema — reverse all SPEC-10 changes."""
    op.drop_table('meeting_participants')
    op.drop_table('meeting_teams')
    op.drop_table('members')

    op.drop_constraint('fk_meetings_company_id', 'meetings', type_='foreignkey')
    op.drop_constraint('fk_meetings_created_by', 'meetings', type_='foreignkey')
    op.drop_index(op.f('ix_meetings_session_id'), table_name='meetings')

    op.alter_column('meetings', 'summary',
                    existing_type=sa.Text(), type_=sa.VARCHAR(), existing_nullable=True)
    op.alter_column('meetings', 'transcript',
                    existing_type=sa.Text(), type_=sa.VARCHAR(), existing_nullable=True)
    op.alter_column('meetings', 'error_message',
                    existing_type=sa.Text(), type_=sa.VARCHAR(), existing_nullable=True)
    op.execute(
        "ALTER TABLE meetings ALTER COLUMN status TYPE VARCHAR USING status::varchar"
    )
    op.alter_column('meetings', 'created_at',
                    existing_type=sa.DateTime(timezone=True),
                    type_=postgresql.TIMESTAMP(),
                    nullable=False)
    op.drop_column('meetings', 'created_by')
    op.drop_column('meetings', 'company_id')
    op.drop_column('meetings', 'scheduled_time')
    op.execute("ALTER TABLE meetings ALTER COLUMN id TYPE VARCHAR USING id::varchar")

    op.drop_table('teams')
    op.drop_table('users')
    op.drop_table('companies')
    op.execute("DROP TYPE IF EXISTS meetingstatus")
    op.execute("DROP TYPE IF EXISTS userrole")
