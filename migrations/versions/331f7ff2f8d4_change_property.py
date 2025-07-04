"""change property

Revision ID: 331f7ff2f8d4
Revises: a4fa0113b853
Create Date: 2025-07-04 11:52:09.934771

"""
from alembic import op
import sqlalchemy as sa


from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '331f7ff2f8d4'
down_revision = 'a4fa0113b853'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('contact', schema=None) as batch_op:
        # Drop the existing unique constraint — adjust name if needed
        batch_op.drop_constraint('UQ__contact__AB6E6164405B0FED', type_='unique')

        # Alter column if necessary (optional)
        batch_op.alter_column('email',
                              existing_type=sa.String(length=100),
                              nullable=False)

def downgrade():
    with op.batch_alter_table('contact', schema=None) as batch_op:
        # Recreate the unique constraint (for rollback)
        batch_op.create_unique_constraint('UQ__contact__AB6E6164405B0FED', ['email'])

        batch_op.alter_column('email',
                              existing_type=sa.String(length=100),
                              nullable=False)

    # ### end Alembic commands ###
