SELECT
    *
FROM
    people p

    {% if transaction_id %}
    JOIN m_people_transactions mpt
    ON p.id = mpt.person_id
{% endif %}
WHERE
    p.id IN (
        SELECT
            player_id
        FROM
            m_player_parent
    ) {% if transaction_id %}
        AND mpt.transaction_id = '{{transaction_id}}'
    {% endif %};
