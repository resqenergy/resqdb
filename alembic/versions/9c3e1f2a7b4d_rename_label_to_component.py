"""Rename label to component; replace is_bus by role; add directional labels

Revision ID: 9c3e1f2a7b4d
Revises: 47a17d180c5c
Create Date: 2026-10-01 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9c3e1f2a7b4d"
down_revision: Union[str, Sequence[str], None] = "47a17d180c5c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Views and their SQL functions still reference the old label table and roles are only set for buses afterwards;
    run `python main.py views recreate` to reload components and recreate functions and views.
    """
    # Views without SQL file anymore (renamed to flow_timeseries / replaced by pytest check)
    op.execute(
        "DROP MATERIALIZED VIEW IF EXISTS public.input_timeseries, public.missing_labels"
    )
    op.execute("ALTER TABLE public.label RENAME TO component")
    op.execute(
        "ALTER TABLE public.component RENAME CONSTRAINT pk_label TO pk_component"
    )
    op.execute(
        "ALTER TABLE public.component RENAME CONSTRAINT uq_label_component TO uq_component_component"
    )
    op.execute("ALTER SEQUENCE public.label_id_seq RENAME TO component_id_seq")
    op.add_column(
        "component", sa.Column("role", sa.String(), nullable=True), schema="public"
    )
    op.add_column(
        "component", sa.Column("label_in", sa.String(), nullable=True), schema="public"
    )
    op.add_column(
        "component", sa.Column("label_out", sa.String(), nullable=True), schema="public"
    )
    op.execute("UPDATE public.component SET role = 'bus' WHERE is_bus")
    op.drop_column("component", "is_bus", schema="public")


def downgrade() -> None:
    """Downgrade schema; afterwards recreate views via `python main.py views recreate`."""
    # Views joining component columns directly
    op.execute(
        "DROP MATERIALIZED VIEW IF EXISTS "
        "public.autarky, public.capacities, public.energy_flows, public.production_demand"
    )
    op.add_column(
        "component",
        sa.Column("is_bus", sa.Boolean(), nullable=False, server_default=sa.false()),
        schema="public",
    )
    op.alter_column("component", "is_bus", server_default=None, schema="public")
    op.execute("UPDATE public.component SET is_bus = (role IS NOT DISTINCT FROM 'bus')")
    op.drop_column("component", "label_out", schema="public")
    op.drop_column("component", "label_in", schema="public")
    op.drop_column("component", "role", schema="public")
    op.execute("ALTER SEQUENCE public.component_id_seq RENAME TO label_id_seq")
    op.execute(
        "ALTER TABLE public.component RENAME CONSTRAINT uq_component_component TO uq_label_component"
    )
    op.execute(
        "ALTER TABLE public.component RENAME CONSTRAINT pk_component TO pk_label"
    )
    op.execute("ALTER TABLE public.component RENAME TO label")
