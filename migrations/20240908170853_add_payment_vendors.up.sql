ALTER TABLE
    ONLY PUBLIC.transactions
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
