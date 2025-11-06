"""add transaction history

Revision ID: 003
Revises: 002
Create Date: 2025-11-06

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tx_hash', sa.String(length=64), nullable=True),
        sa.Column('tx_type', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('user_address', sa.String(length=100), nullable=False),
        sa.Column('asset_id', sa.String(length=64), nullable=False),
        sa.Column('amount', sa.BigInteger(), nullable=False),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.Column('result_data', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('confirmed_at', sa.DateTime(), nullable=True),
        sa.Column('position_id', sa.Integer(), nullable=True),
        sa.Column('reserve_asset_id', sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for efficient querying
    op.create_index(op.f('ix_transactions_tx_hash'), 'transactions', ['tx_hash'], unique=False)
    op.create_index(op.f('ix_transactions_tx_type'), 'transactions', ['tx_type'], unique=False)
    op.create_index(op.f('ix_transactions_user_address'), 'transactions', ['user_address'], unique=False)
    op.create_index(op.f('ix_transactions_asset_id'), 'transactions', ['asset_id'], unique=False)
    op.create_index(op.f('ix_transactions_created_at'), 'transactions', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_transactions_created_at'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_asset_id'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_user_address'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_tx_type'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_tx_hash'), table_name='transactions')
    
    # Drop table
    op.drop_table('transactions')
