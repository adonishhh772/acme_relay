-- 30-day demo metric series for dashboard line charts (AM + ops KPIs).
DELETE FROM metric_snapshots
WHERE metric_name IN (
    'open_issues', 'critical_issues', 'sla_at_risk', 'risk_score', 'customers_at_risk'
);

WITH days AS (
    SELECT generate_series(0, 29) AS day_offset
),
active_customers AS (
    SELECT external_id FROM customers WHERE is_active
),
series AS (
    SELECT
        ac.external_id,
        (CURRENT_DATE - (d.day_offset || ' days')::interval)::date AS metric_date,
        CASE ac.external_id
            WHEN 'VAULTLEDGER' THEN greatest(1, 1 + (29 - d.day_offset) / 8)
            WHEN 'AURORABANK' THEN greatest(1, 1 + ((29 - d.day_offset) % 5) / 3)
            ELSE 1
        END AS open_issues,
        CASE ac.external_id
            WHEN 'VAULTLEDGER' THEN CASE WHEN d.day_offset < 14 THEN 1 ELSE 0 END
            ELSE 0
        END AS critical_issues,
        CASE ac.external_id
            WHEN 'VAULTLEDGER' THEN CASE WHEN d.day_offset < 10 THEN 1 ELSE 0 END
            WHEN 'AURORABANK' THEN CASE WHEN d.day_offset < 5 THEN 1 ELSE 0 END
            ELSE 0
        END AS sla_at_risk,
        CASE ac.external_id
            WHEN 'VAULTLEDGER' THEN 40 + (29 - d.day_offset)
            WHEN 'AURORABANK' THEN 25 + ((29 - d.day_offset) % 12)
            ELSE 15 + ((29 - d.day_offset) % 8)
        END AS risk_score
    FROM active_customers ac
    CROSS JOIN days d
),
expanded AS (
    SELECT
        'open_issues'::text AS metric_name,
        open_issues::numeric AS metric_value,
        jsonb_build_object('customer_external_id', external_id, 'grain', 'day') AS labels,
        (metric_date::timestamp + interval '12 hours') AS captured_at
    FROM series
    UNION ALL
    SELECT
        'critical_issues',
        critical_issues::numeric,
        jsonb_build_object('customer_external_id', external_id, 'grain', 'day'),
        (metric_date::timestamp + interval '12 hours')
    FROM series
    UNION ALL
    SELECT
        'sla_at_risk',
        sla_at_risk::numeric,
        jsonb_build_object('customer_external_id', external_id, 'grain', 'day'),
        (metric_date::timestamp + interval '12 hours')
    FROM series
    UNION ALL
    SELECT
        'risk_score',
        risk_score::numeric,
        jsonb_build_object('customer_external_id', external_id, 'grain', 'day'),
        (metric_date::timestamp + interval '12 hours')
    FROM series
    UNION ALL
    SELECT
        'customers_at_risk',
        COUNT(*) FILTER (WHERE risk_score >= 40)::numeric,
        jsonb_build_object('scope', 'portfolio', 'grain', 'day'),
        (metric_date::timestamp + interval '12 hours')
    FROM series
    GROUP BY metric_date
)
INSERT INTO metric_snapshots (metric_name, metric_value, labels, captured_at)
SELECT metric_name, metric_value, labels, captured_at FROM expanded;
