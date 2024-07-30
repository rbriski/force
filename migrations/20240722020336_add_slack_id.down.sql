DROP INDEX uniq_slack_id_idx;
ALTER TABLE
    ONLY PUBLIC.people DROP column IF EXISTS slack_id;
