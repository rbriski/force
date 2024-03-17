CREATE TABLE public.brackets (
    name CHARACTER VARYING NOT NULL,
    email CHARACTER VARYING,
    bracket_ids CHARACTER VARYING,
    id uuid NOT NULL,
    created_at TIMESTAMP without TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP without TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

ALTER TABLE
    ONLY public.brackets
ADD
    CONSTRAINT brackets_pkey PRIMARY KEY (id);
