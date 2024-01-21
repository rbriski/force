CREATE TABLE public.events (
    at_id character varying NOT NULL,
    name character varying NOT NULL,
    date date,
    description character varying,
    id uuid NOT NULL,
    created_at timestamp without time zone default CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone default CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE public.m_people_transactions (
    person_id uuid NOT NULL,
    transaction_id uuid NOT NULL,
    id uuid NOT NULL,
    created_at timestamp without time zone default CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone default CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE public.m_player_parent (
    player_id uuid NOT NULL,
    parent_id uuid NOT NULL,
    id uuid NOT NULL,
    created_at timestamp without time zone default CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone default CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE public.people (
    at_id character varying NOT NULL,
    name character varying NOT NULL,
    description character varying,
    email character varying,
    phone character varying,
    id uuid NOT NULL,
    created_at timestamp without time zone default CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone default CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE public.transactions (
    at_id character varying NOT NULL,
    event_id uuid,
    amount integer NOT NULL,
    description character varying,
    debit boolean NOT NULL,
    id uuid NOT NULL,
    created_at timestamp without time zone default CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone default CURRENT_TIMESTAMP NOT NULL
);

ALTER TABLE
    ONLY public.events
ADD
    CONSTRAINT events_pkey PRIMARY KEY (id);

ALTER TABLE
    ONLY public.m_people_transactions
ADD
    CONSTRAINT m_people_transactions_pkey PRIMARY KEY (person_id, transaction_id, id);

ALTER TABLE
    ONLY public.m_player_parent
ADD
    CONSTRAINT m_player_parent_pkey PRIMARY KEY (player_id, parent_id, id);

ALTER TABLE
    ONLY public.people
ADD
    CONSTRAINT people_pkey PRIMARY KEY (id);

ALTER TABLE
    ONLY public.transactions
ADD
    CONSTRAINT transactions_pkey PRIMARY KEY (id);

ALTER TABLE
    ONLY public.m_people_transactions
ADD
    CONSTRAINT m_people_transactions_person_id_fkey FOREIGN KEY (person_id) REFERENCES public.people(id);

ALTER TABLE
    ONLY public.m_people_transactions
ADD
    CONSTRAINT m_people_transactions_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES public.transactions(id);

ALTER TABLE
    ONLY public.m_player_parent
ADD
    CONSTRAINT m_player_parent_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.people(id);

ALTER TABLE
    ONLY public.m_player_parent
ADD
    CONSTRAINT m_player_parent_player_id_fkey FOREIGN KEY (player_id) REFERENCES public.people(id);

ALTER TABLE
    ONLY public.transactions
ADD
    CONSTRAINT transactions_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id);