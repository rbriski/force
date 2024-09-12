ALTER TABLE
    PUBLIC.transactions DROP constraint IF EXISTS uniq_vendor_name_txn_id;
ALTER TABLE
    ONLY PUBLIC.transactions DROP column IF EXISTS vendor_name,
    DROP column IF EXISTS vendor_txn_id;
DROP INDEX IF EXISTS uniq_vendor_name_txn_id;
