"""Add foreign keys to chats and messages

Revision ID: 2229705dc9fd
Revises: b4dc58d4648e
Create Date: 2024-10-26 20:54:06.994503

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2229705dc9fd'
down_revision: Union[str, None] = 'b4dc58d4648e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_cmetadata_gin', table_name='langchain_pg_embedding', postgresql_using='gin')
    op.drop_index('ix_langchain_pg_embedding_id', table_name='langchain_pg_embedding')
    op.drop_table('langchain_pg_embedding')
    op.drop_table('langchain_pg_collection')
    op.create_foreign_key(None, 'chats', 'users', ['user_id'], ['id'])
    op.create_foreign_key(None, 'messages', 'chats', ['chat_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'messages', type_='foreignkey')
    op.drop_constraint(None, 'chats', type_='foreignkey')
    op.create_table('langchain_pg_collection',
    sa.Column('uuid', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('cmetadata', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('uuid', name='langchain_pg_collection_pkey'),
    sa.UniqueConstraint('name', name='langchain_pg_collection_name_key'),
    postgresql_ignore_search_path=False
    )
    op.create_table('langchain_pg_embedding',
    sa.Column('id', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('collection_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('embedding', sa.NullType(), autoincrement=False, nullable=True),
    sa.Column('document', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('cmetadata', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['collection_id'], ['langchain_pg_collection.uuid'], name='langchain_pg_embedding_collection_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='langchain_pg_embedding_pkey')
    )
    op.create_index('ix_langchain_pg_embedding_id', 'langchain_pg_embedding', ['id'], unique=True)
    op.create_index('ix_cmetadata_gin', 'langchain_pg_embedding', ['cmetadata'], unique=False, postgresql_using='gin')
    # ### end Alembic commands ###
