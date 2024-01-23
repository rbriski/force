CREATE UNIQUE INDEX uniq_parent_id_player_id_idx ON m_player_parent(parent_id, player_id);

CREATE UNIQUE INDEX uniq_person_id_transaction_id_idx ON m_people_transactions(person_id, transaction_id);