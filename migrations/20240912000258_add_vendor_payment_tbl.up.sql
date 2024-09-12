ALTER TABLE
    PUBLIC.transactions DROP constraint IF EXISTS uniq_vendor_name_txn_id;
ALTER TABLE
    ONLY PUBLIC.transactions DROP column IF EXISTS vendor_name,
    DROP column IF EXISTS vendor_txn_id;
DROP INDEX IF EXISTS uniq_vendor_name_txn_id;
CREATE TABLE PUBLIC.vendor_payments (
        transaction_id uuid,
        amount DECIMAL NOT NULL,
        sender CHARACTER VARYING NOT NULL,
        vendor_txn_id CHARACTER VARYING NOT NULL,
        vendor_name CHARACTER VARYING NOT NULL,
        id uuid NOT NULL,
        transaction_date DATE NOT NULL,
        created_at TIMESTAMP without TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
        updated_at TIMESTAMP without TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
    );
ALTER TABLE
    PUBLIC.vendor_payments
ADD
    constraint uniq_vendor_name_txn_id UNIQUE (
        vendor_name,
        vendor_txn_id
    );
ALTER TABLE
    vendor_payments
ADD
    constraint fk_vendor_payments_transaction foreign key (transaction_id) references PUBLIC.transactions(id);
