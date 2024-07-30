ALTER TABLE
    ONLY PUBLIC.people
ADD
    column IF NOT EXISTS slack_id CHARACTER VARYING;
CREATE UNIQUE INDEX uniq_slack_id_idx
    ON people(slack_id);
