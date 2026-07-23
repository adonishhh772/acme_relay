-- Account management enrichment for Relay customers + chart metrics.
ALTER TABLE customers ADD COLUMN IF NOT EXISTS support_manager VARCHAR(255);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS account_manager VARCHAR(128);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS contract_value_gbp NUMERIC(14, 2);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS renewal_date DATE;

DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'customers_contract_value_non_negative'
    ) THEN
        ALTER TABLE customers ADD CONSTRAINT customers_contract_value_non_negative
            CHECK (contract_value_gbp IS NULL OR contract_value_gbp >= 0);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_customers_renewal_date
    ON customers (renewal_date)
    WHERE renewal_date IS NOT NULL AND is_active = true;

CREATE INDEX IF NOT EXISTS idx_metric_snapshots_labels_gin
    ON metric_snapshots USING GIN (labels);

INSERT INTO schema_migrations (version, description)
VALUES ('005_account_management', 'AM fields on customers + metrics indexes')
ON CONFLICT (version) DO NOTHING;
