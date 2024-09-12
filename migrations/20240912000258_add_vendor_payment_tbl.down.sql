ALTER TABLE
    PUBLIC.vendor_payments DROP constraint IF EXISTS uniq_vendor_name_txn_id;
ALTER TABLE
    PUBLIC.vendor_payments DROP constraint IF EXISTS fk_vendor_payments_transaction;
DROP TABLE IF EXISTS PUBLIC.vendor_payments;
ALTER TABLE
    PUBLIC.transactions
ADD
    column IF NOT EXISTS vendor_name CHARACTER VARYING,
ADD
    column IF NOT EXISTS vendor_txn_id CHARACTER VARYING;
ALTER TABLE
    PUBLIC.transactions
ADD
    constraint uniq_vendor_name_txn_id UNIQUE (
        vendor_name,
        vendor_txn_id
    );
