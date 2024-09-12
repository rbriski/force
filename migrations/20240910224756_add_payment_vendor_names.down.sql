ALTER TABLE
    ONLY PUBLIC.people DROP column IF EXISTS paypal_name,
    DROP column IF EXISTS venmo_name;
