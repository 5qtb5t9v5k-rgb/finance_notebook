-- ============================================================
-- Finance Coach — Supabase Schema
-- Aja tämä Supabase SQL Editorissa ennen migraatiota
-- ============================================================

-- Note codes: lyhenteiden sanasto
-- note_code on kontekstuaalinen — sama kirjain eri kategoriassa = eri asia
-- esim. G = "Car Gas" Transportissa, "Gifts" Shoppingissa
CREATE TABLE IF NOT EXISTS note_codes (
    category_en     TEXT NOT NULL,
    note_code       TEXT NOT NULL,
    meaning_en      TEXT NOT NULL,
    meaning_fi      TEXT NOT NULL,
    second_cat_fi   TEXT NOT NULL,   -- lopullinen arvo transactions-taulussa
    PRIMARY KEY (category_en, note_code)
);

-- Kategoriat
CREATE TABLE IF NOT EXISTS categories (
    category_en     TEXT PRIMARY KEY,
    category_fi     TEXT NOT NULL UNIQUE
);

-- Merchant-säännöt: opittu historia
-- (merchant, note_code) → (category_en, second_cat_fi)
-- note_code voi olla tyhjä string '' — tarkoittaa "ei notea"
CREATE TABLE IF NOT EXISTS merchant_rules (
    id              BIGSERIAL PRIMARY KEY,
    merchant        TEXT NOT NULL,
    note_code       TEXT NOT NULL DEFAULT '',
    category_en     TEXT NOT NULL,
    category_fi     TEXT NOT NULL,
    second_cat_fi   TEXT NOT NULL DEFAULT '',
    confidence      REAL NOT NULL DEFAULT 1.0,   -- 0-1, laskee jos käyttäjä korjaa
    source          TEXT NOT NULL DEFAULT 'historical', -- 'historical'|'manual'|'llm'
    hit_count       INTEGER NOT NULL DEFAULT 0,
    last_seen       DATE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (merchant, note_code)
);

-- Tapahtumat
CREATE TABLE IF NOT EXISTS transactions (
    id              TEXT PRIMARY KEY,            -- hash(date|merchant|amount|time)
    date            DATE NOT NULL,
    time            TEXT NOT NULL DEFAULT '',
    merchant        TEXT NOT NULL,
    amount          REAL NOT NULL,
    adjusted_amount REAL NOT NULL,
    cost_allocation REAL NOT NULL DEFAULT 1.0,
    currency        TEXT NOT NULL DEFAULT 'EUR',
    category_en     TEXT NOT NULL DEFAULT '',
    category_fi     TEXT NOT NULL DEFAULT '',
    second_cat_fi   TEXT NOT NULL DEFAULT '',
    note_code       TEXT NOT NULL DEFAULT '',
    note_raw        TEXT NOT NULL DEFAULT '',    -- alkuperäinen Curve-notes
    card_last4      INTEGER,
    card_name       TEXT,
    rule_source     TEXT NOT NULL DEFAULT 'manual',  -- miten kategorisoitiin
    needs_review    BOOLEAN NOT NULL DEFAULT FALSE,
    locked          BOOLEAN NOT NULL DEFAULT FALSE,  -- TRUE = käsin korjattu, CSV-upload ei ylikirjoita
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Indeksit kyselynopeutta varten
CREATE INDEX IF NOT EXISTS idx_transactions_date        ON transactions (date DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_category    ON transactions (category_fi);
CREATE INDEX IF NOT EXISTS idx_transactions_merchant    ON transactions (merchant);
CREATE INDEX IF NOT EXISTS idx_transactions_needs_review ON transactions (needs_review) WHERE needs_review = TRUE;
CREATE INDEX IF NOT EXISTS idx_merchant_rules_merchant  ON merchant_rules (merchant);

-- ============================================================
-- Seed: kategoriat
-- ============================================================
INSERT INTO categories (category_en, category_fi) VALUES
    ('General',           'Harrastukset'),
    ('Business Services', 'Koulutus, Kirjallisuus & Kehittäminen'),
    ('Entertainment',     'Tapahtumat & Viihde'),
    ('Transport',         'Autoilu & Liikkuminen'),
    ('Shopping',          'Ostokset'),
    ('Eating Out',        'Ulkona syöminen'),
    ('Groceries',         'Ruokakauppa'),
    ('Bills',             'Striimaus & Palvelut'),
    ('Health',            'Terveys'),
    ('Travel',            'Matkailu')
ON CONFLICT (category_en) DO NOTHING;

-- ============================================================
-- Seed: note codes — kaikki lyhenteet selityksineen
-- ============================================================
INSERT INTO note_codes (category_en, note_code, meaning_en, meaning_fi, second_cat_fi) VALUES
    -- Entertainment
    ('Entertainment', 'F',  'Family',            'Perhe',                    'Tapahtumat & Viihde: Perhe'),
    ('Entertainment', 'P',  'Personal',          'Henkilökohtainen',         'Tapahtumat & Viihde: Henkilökohtainen'),
    -- Transport
    ('Transport',     'G',  'Car Gas',           'Auton Polttoaine',         'Auton Polttoaine'),
    ('Transport',     'M',  'Car Maintenance',   'Auton Huollot & Ylläpito', 'Auton Huollot & Ylläpito'),
    ('Transport',     'P',  'Public Transport',  'Julkinen liikenne',        'Julkinen liikenne'),
    -- Shopping
    ('Shopping',      'H',  'Home / House',      'Koti',                     'Ostokset: Koti'),
    ('Shopping',      'P',  'Personal',          'Henkilökohtainen',         'Ostokset: Henkilökohtainen'),
    ('Shopping',      'RT', 'Renovating & Tools','Remontointi',              'Ostokset: Remontointi'),
    ('Shopping',      'F',  'Family',            'Perhe',                    'Ostokset: Perhe'),
    ('Shopping',      'G',  'Gifts',             'Lahjat',                   'Ostokset: Lahjat'),
    ('Shopping',      'K',  'Kids',              'Lapset',                   'Ostokset: Lapset'),
    -- Eating Out
    ('Eating Out',    'S',  'Snacks & Soda',     'Välipalat & Virvoikkeet',  'Välipalat & Virvoikkeet'),
    ('Eating Out',    'R',  'Restaurants',       'Ravintolat',               'Ravintolat'),
    -- Health
    ('Health',        'F',  'Family',            'Perhe',                    'Terveys: Perhe'),
    ('Health',        'P',  'Personal',          'Henkilökohtainen',         'Terveys: Henkilökohtainen'),
    -- Travel
    ('Travel',        'F',  'Family',            'Perhe',                    'Matkailu: Perhe'),
    ('Travel',        'P',  'Personal',          'Henkilökohtainen',         'Matkailu: Henkilökohtainen')
ON CONFLICT (category_en, note_code) DO NOTHING;
