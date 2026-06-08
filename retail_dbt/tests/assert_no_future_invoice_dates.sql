-- Singular test: invoices must not be dated in the future. Returns offending rows;
-- the test passes when zero rows come back.

select invoice_id, invoice_date
from {{ ref('fct_invoice_lines') }}
where invoice_date > current_date
