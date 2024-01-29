CREATE INDEX if NOT EXISTS m_people_transactions_person_id_idx
ON m_people_transactions(
    person_id,
    id
);
CREATE INDEX if NOT EXISTS m_people_transactions_transaction_id_idx
ON m_people_transactions(
    transaction_id,
    id
);
