"""
create cart table
"""

from yoyo import step

__depends__ = {'20260226_02_sEpiR-timestamp-function'}

steps = [
    step(
        """
        create table carts
        (
            id         uuid primary key     default gen_random_uuid(),
            created_at timestamptz not null default now(),
            updated_at timestamptz not null default now()
        );

        create table cart_items
        (
            id         uuid primary key     default gen_random_uuid(),
            cart_id    uuid        not null references carts (id) on delete cascade,
            product_id integer     not null references products (id),
            quantity   integer     not null check (quantity > 0),
            created_at timestamptz not null default now(),
            updated_at timestamptz not null default now(),
            unique (cart_id, product_id)
        );

        create index idx_cart_items_cart_id on cart_items (cart_id);
        create index idx_cart_items_product_id on cart_items (product_id);

        CREATE OR REPLACE FUNCTION set_updated_at()
            RETURNS TRIGGER AS
        $$
        BEGIN
            IF NEW IS DISTINCT FROM OLD THEN
                NEW.updated_at = now();
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        create trigger trigger_carts_updated_at
            before update
            on carts
            for each row
        execute function set_updated_at();

        create trigger trigger_cart_items_updated_at
            before update
            on cart_items
            for each row
        execute function set_updated_at();
        """
    )
]
