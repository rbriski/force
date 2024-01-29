WITH people_per AS (
    SELECT
        mpt.transaction_id,
        COUNT(*) AS attendees
    FROM
        {{ g_m_player_transactions_tbl }}
        mpt
        JOIN {{ g_people_tbl }}
        p
        ON mpt.person_id = p.id
        JOIN {{ g_transactions_tbl }}
        t
        ON mpt.transaction_id = t.id
    GROUP BY
        1
) {%- if person_id -%},
    user_transactions AS (
        SELECT
            *
        FROM
            {{ g_m_player_transactions_tbl }}
            mpt
            JOIN {{ g_people_tbl }}
            p
            ON mpt.person_id = p.id
        WHERE
            p.id = '{{person_id}}'
    )
{%- endif -%}
SELECT
    t.id AS t_id,
    t.created_at AS t_created_at,
    t.updated_at AS t_updated_at,
    t.at_id AS t_at_id,
    t.event_id AS t_event_id,
    t.amount AS t_amount,
    t.description AS t_description,
    t.debit AS t_debit,
    attendees AS t_attendees,
    t.amount / attendees AS t_per_person,
    e.id AS e_id,
    e.created_at AS e_created_at,
    e.updated_at AS e_updated_at,
    e.at_id AS e_at_id,
    e.name AS e_name,
    e.date AS e_date,
    e.description AS e_description
FROM
    people_per pp

    {% if person_id -%}
    JOIN user_transactions ut
    ON pp.transaction_id = ut.transaction_id
{%- endif %}
JOIN {{ g_transactions_tbl }}
t
ON pp.transaction_id = t.id
LEFT JOIN {{ g_events_tbl }}
e
ON t.event_id = e.id
ORDER BY
    t.created_at DESC;
