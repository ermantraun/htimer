"""add models

Revision ID: 15f837e8f31c
Revises: 
Create Date: 2026-02-03 15:48:10.749213
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '15f837e8f31c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema."""

    # ENUMs
    userrole_enum = postgresql.ENUM('ADMIN', 'USER', name='userrole', )
    userstatus_enum = postgresql.ENUM('ACTIVE', 'BLOCKED', 'ARCHIVED', name='userstatus', )
    projectstatus_enum = postgresql.ENUM('ACTIVE', 'ARCHIVED', 'BLOCKED', 'COMPLETED', name='projectstatus', )
    stagestatus_enum = postgresql.ENUM('ACTIVE', 'COMPLETED', 'ARCHIVED', name='stagestatus', )
    subscriptionstatus_enum = postgresql.ENUM('ACTIVE', 'UNACTIVE', 'EXPIRED', 'CANCELLED', name='subscriptionstatus', )
    paymentstatus_enum = postgresql.ENUM('PENDING', 'COMPLETED', 'FAILED', 'REFUNDED', name='paymentstatus', )
    paymentmethod_enum = postgresql.ENUM('CREDIT_CARD', 'BANK_TRANSFER', 'CRYPTOCURRENCY', name='paymentmethod', )
    currency_enum = postgresql.ENUM('RUB', name='currencyenum', )
    taskstatus_enum = postgresql.ENUM('PENDING', 'IN_PROGRESS', 'COMPLETED', 'ARCHIVED', name='taskstatus', )



    # Users
    op.create_table(
        'users',
        sa.Column('uuid', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(100), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('creator_uuid', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.uuid', ondelete='CASCADE'), nullable=True),
        sa.Column('role', userrole_enum, nullable=False),
        sa.Column('status', userstatus_enum, nullable=False),
        sa.Column('created_at', sa.Date(), nullable=False),
        sa.Column('last_login', sa.Date(), nullable=True),
        sa.CheckConstraint("(role='ADMIN') OR (role='USER' AND creator_uuid IS NOT NULL)", name='check_user_creator_for_user_role')
    )

    # Projects
    op.create_table(
        'projects',
        sa.Column('uuid', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(1000), nullable=True),
        sa.Column('creator_uuid', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.uuid', ondelete='CASCADE'), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('status', projectstatus_enum, nullable=False),
        sa.Column('created_at', sa.Date(), nullable=False),
        sa.UniqueConstraint('creator_uuid', 'name', name='uq_creator_project_name'),
        sa.CheckConstraint('start_date IS NULL OR end_date IS NULL OR start_date <= end_date', name='check_project_start_end_dates')
    )

    # Memberships
    op.create_table(
        'memberships',
        sa.Column('user_uuid', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.uuid', ondelete='CASCADE'), nullable=False),
        sa.Column('project_uuid', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.uuid', ondelete='CASCADE'), nullable=False),
        sa.Column('joined_at', sa.Date(), nullable=False),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.uuid', ondelete='CASCADE'), nullable=False),
        sa.PrimaryKeyConstraint('user_uuid', 'project_uuid')
    )

    # Stages
    op.create_table(
        'stages',
        sa.Column('uuid', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(1000), nullable=True),
        sa.Column('creator_uuid', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.uuid', ondelete='CASCADE'), nullable=False),
        sa.Column('project_uuid', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.uuid', ondelete='CASCADE'), nullable=True),
        sa.Column('parent_uuid', postgresql.UUID(as_uuid=True), sa.ForeignKey('stages.uuid', ondelete='CASCADE'), nullable=True),
        sa.Column('created_at', sa.Date(), nullable=False),
        sa.Column('main_path', sa.Boolean(), nullable=False),
        sa.Column('status', stagestatus_enum, nullable=False),
        sa.CheckConstraint("main_path OR parent_uuid IS NOT NULL", name="ck_stage_main_path_boolean")
    )

    # Subscriptions
    op.create_table(
        'subscriptions',
        sa.Column('uuid', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_uuid', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.uuid', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('created_at', sa.Date(), nullable=False),
        sa.Column('auto_renew', sa.Boolean(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('status', subscriptionstatus_enum, nullable=False),
        sa.CheckConstraint('start_date IS NULL OR end_date IS NULL OR start_date <= end_date', name='check_subscription_start_end_dates')
    )

    # Daily Logs
    op.create_table(
        'daily_logs',
        sa.Column('uuid', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('creator_uuid', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.uuid', ondelete='CASCADE'), nullable=False),
        sa.Column('project_uuid', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.uuid', ondelete='CASCADE'), nullable=False),
        sa.Column('substage_uuid', postgresql.UUID(as_uuid=True), sa.ForeignKey('stages.uuid', ondelete='CASCADE'), nullable=True),
        sa.Column('created_at', sa.Date(), nullable=False),
        sa.Column('updated_at', sa.Date(), nullable=True),
        sa.Column('draft', sa.Boolean(), nullable=False),
        sa.Column('hours_spent', sa.Float(), nullable=False),
        sa.Column('description', sa.String(2000), nullable=False),
        sa.UniqueConstraint('creator_uuid', 'project_uuid', 'created_at', name='uq_creator_project_dailylog_date')
    )

    # Payments
    op.create_table(
        'payments',
        sa.Column('uuid', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('subscription_uuid', postgresql.UUID(as_uuid=True), sa.ForeignKey('subscriptions.uuid', ondelete='CASCADE'), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', currency_enum, nullable=False),
        sa.Column('status', paymentstatus_enum, nullable=False),
        sa.Column('payment_method', paymentmethod_enum, nullable=True),
        sa.Column('created_at', sa.Date(), nullable=False),
        sa.CheckConstraint("amount >= 0", name="ck_payment_amount_positive")
    )

    # Tasks
    op.create_table(
        'tasks',
        sa.Column('uuid', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(1000), nullable=True),
        sa.Column('creator_uuid', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.uuid', ondelete='CASCADE'), nullable=False),
        sa.Column('substage_uuid', postgresql.UUID(as_uuid=True), sa.ForeignKey('stages.uuid', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.Date(), nullable=False),
        sa.Column('status', taskstatus_enum, nullable=False),
        sa.Column('completion_date', sa.Date(), nullable=True),
        sa.Column('working_days', postgresql.ARRAY(sa.Date()), nullable=False)
    )

    # Files
    op.create_table(
        'files',
        sa.Column('uuid', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('uri', sa.String(255), nullable=False),
        sa.Column('uploaded_at', sa.Date(), nullable=False),
        sa.Column('daily_log_uuid', postgresql.UUID(as_uuid=True), sa.ForeignKey('daily_logs.uuid', ondelete='CASCADE'), nullable=False)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('files')
    op.drop_table('tasks')
    op.drop_table('payments')
    op.drop_table('daily_logs')
    op.drop_table('subscriptions')
    op.drop_table('stages')
    op.drop_table('memberships')
    op.drop_table('projects')
    op.drop_table('users')

    # Drop enums
    postgresql.ENUM(name='userrole').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='userstatus').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='projectstatus').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='stagestatus').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='subscriptionstatus').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='paymentstatus').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='paymentmethod').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='currencyenum').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='taskstatus').drop(op.get_bind(), checkfirst=True)
