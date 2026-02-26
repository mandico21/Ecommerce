"""
timestamp_function
"""

from yoyo import step

__depends__ = {'20260226_01_mSxWF-create-product-table'}

steps = [
    step(
        """
        CREATE OR REPLACE FUNCTION set_updated_at()
            RETURNS TRIGGER AS
        $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """,
        """
        DROP FUNCTION IF EXISTS set_updated_at();
        """
    ),
]
