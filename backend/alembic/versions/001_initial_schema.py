"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2025-11-06

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
    """Create initial tables."""
    
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('address', sa.String(length=100), nullable=False),
        sa.Column('health_factor', sa.BigInteger(), nullable=True, comment='Health factor in RAY precision (10^27)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('address')
    )
    op.create_index(op.f('ix_users_address'), 'users', ['address'], unique=True)
    
    # Reserve states table
    op.create_table(
        'reserve_states',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('asset_id', sa.String(length=64), nullable=False, comment='Liquid asset ID'),
        sa.Column('utxo_id', sa.String(length=100), nullable=False, comment='Current Reserve UTXO (txid:vout)'),
        sa.Column('total_liquidity', sa.BigInteger(), nullable=False, comment='Total supplied assets (satoshis)'),
        sa.Column('total_borrowed', sa.BigInteger(), nullable=False, comment='Total borrowed assets (satoshis)'),
        sa.Column('liquidity_index', sa.BigInteger(), nullable=False, comment='Cumulative supply interest index (RAY)'),
        sa.Column('variable_borrow_index', sa.BigInteger(), nullable=False, comment='Cumulative borrow interest index (RAY)'),
        sa.Column('current_liquidity_rate', sa.BigInteger(), nullable=False, comment='Current supply rate per second (RAY)'),
        sa.Column('current_variable_borrow_rate', sa.BigInteger(), nullable=False, comment='Current borrow rate per second (RAY)'),
        sa.Column('last_update_timestamp', sa.BigInteger(), nullable=False, comment='Last update timestamp (Unix seconds)'),
        sa.Column('reserve_factor', sa.BigInteger(), nullable=False, comment='Protocol fee percentage (RAY)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('asset_id')
    )
    op.create_index(op.f('ix_reserve_states_asset_id'), 'reserve_states', ['asset_id'], unique=True)


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index(op.f('ix_reserve_states_asset_id'), table_name='reserve_states')
    op.drop_table('reserve_states')
    op.drop_index(op.f('ix_users_address'), table_name='users')
    op.drop_table('users')
