-- =====================================================================
-- MOONEY - Schema PostgreSQL Completo
-- =====================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto"; -- gen_random_uuid()

-- ---------- ENUMS PRINCIPAIS ----------
DO $$ BEGIN
    CREATE TYPE account_type AS ENUM ('checking', 'savings', 'credit_card', 'investment', 'cash', 'other');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE transaction_type AS ENUM ('income', 'expense', 'transfer');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE import_status AS ENUM ('pending', 'processing', 'done', 'failed', 'reverted');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ---------- USUARIOS ----------
CREATE TABLE IF NOT EXISTS users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name          VARCHAR(120) NOT NULL,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT         NOT NULL,
    currency      CHAR(3)      NOT NULL DEFAULT 'BRL',
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- ---------- INSTITUICOES (catalogo de bancos) ----------
CREATE TABLE IF NOT EXISTS institutions (
    id         SERIAL PRIMARY KEY,
    code       VARCHAR(30)  NOT NULL UNIQUE,
    name       VARCHAR(100) NOT NULL,
    bank_code  VARCHAR(10),
    parser_key VARCHAR(50),
    logo_url   TEXT,
    is_active  BOOLEAN NOT NULL DEFAULT TRUE
);

-- ---------- CONTAS ----------
CREATE TABLE IF NOT EXISTS accounts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    institution_id  INT  REFERENCES institutions(id),
    name            VARCHAR(100) NOT NULL,
    type            account_type NOT NULL DEFAULT 'checking',
    initial_balance NUMERIC(14,2) NOT NULL DEFAULT 0,
    credit_limit    NUMERIC(14,2),
    include_in_total BOOLEAN NOT NULL DEFAULT TRUE,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_accounts_user ON accounts(user_id);

-- ---------- CATEGORIAS ----------
CREATE TABLE IF NOT EXISTS categories (
    id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id   UUID REFERENCES users(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    name      VARCHAR(80) NOT NULL,
    type      transaction_type NOT NULL DEFAULT 'expense',
    color     VARCHAR(9),
    icon      VARCHAR(50),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS idx_categories_user ON categories(user_id);

-- ---------- IMPORTACOES DE EXTRATO ----------
CREATE TABLE IF NOT EXISTS imports (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_id    UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    filename      VARCHAR(255),
    file_hash     CHAR(64) NOT NULL,
    status        import_status NOT NULL DEFAULT 'pending',
    rows_total    INT NOT NULL DEFAULT 0,
    rows_imported INT NOT NULL DEFAULT 0,
    rows_skipped  INT NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (account_id, file_hash)
);

-- ---------- FATURA DE CARTAO DE CREDITO ----------
CREATE TABLE IF NOT EXISTS credit_card_invoices (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id  UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    closing_on  DATE NOT NULL,
    due_on      DATE NOT NULL,
    total       NUMERIC(14,2) NOT NULL DEFAULT 0,
    is_paid     BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (account_id, closing_on)
);

-- ---------- TRANSACOES ----------
CREATE TABLE IF NOT EXISTS transactions (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_id        UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    category_id       UUID REFERENCES categories(id) ON DELETE SET NULL,
    import_id         UUID REFERENCES imports(id) ON DELETE SET NULL,
    invoice_id        UUID REFERENCES credit_card_invoices(id) ON DELETE SET NULL,
    type              transaction_type NOT NULL,
    amount            NUMERIC(14,2) NOT NULL CHECK (amount > 0),
    description       VARCHAR(255) NOT NULL,
    raw_description   TEXT,
    occurred_on       DATE NOT NULL,
    external_id       VARCHAR(100),
    dedupe_hash       CHAR(64) NOT NULL,
    transfer_group_id UUID,
    installment_number SMALLINT,
    installment_total  SMALLINT,
    notes             TEXT,
    metadata          JSONB NOT NULL DEFAULT '{}',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (account_id, dedupe_hash)
);
CREATE INDEX IF NOT EXISTS idx_tx_user_date     ON transactions(user_id, occurred_on DESC);
CREATE INDEX IF NOT EXISTS idx_tx_account_date  ON transactions(account_id, occurred_on DESC);
CREATE INDEX IF NOT EXISTS idx_tx_category      ON transactions(category_id);
CREATE INDEX IF NOT EXISTS idx_tx_transfer      ON transactions(transfer_group_id) WHERE transfer_group_id IS NOT NULL;

-- ---------- REGRAS DE CATEGORIZACAO AUTOMATICA ----------
CREATE TABLE IF NOT EXISTS category_rules (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    pattern     VARCHAR(120) NOT NULL,
    match_type  VARCHAR(10) NOT NULL DEFAULT 'contains' CHECK (match_type IN ('contains','starts_with','regex')),
    priority    INT NOT NULL DEFAULT 0,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE
);

-- ---------- ORCAMENTOS ----------
CREATE TABLE IF NOT EXISTS budgets (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id  UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    period_month DATE NOT NULL CHECK (EXTRACT(DAY FROM period_month) = 1),
    amount_limit NUMERIC(14,2) NOT NULL CHECK (amount_limit >= 0),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, category_id, period_month)
);

-- ---------- TAGS E TRANSACTION_TAGS ----------
CREATE TABLE IF NOT EXISTS tags (
    id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name    VARCHAR(50) NOT NULL,
    UNIQUE (user_id, name)
);

CREATE TABLE IF NOT EXISTS transaction_tags (
    transaction_id UUID REFERENCES transactions(id) ON DELETE CASCADE,
    tag_id         UUID REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (transaction_id, tag_id)
);

-- ---------- METAS / OBJETIVOS ----------
CREATE TABLE IF NOT EXISTS goals (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name           VARCHAR(100) NOT NULL,
    target_amount  NUMERIC(14,2) NOT NULL CHECK (target_amount > 0),
    current_amount NUMERIC(14,2) NOT NULL DEFAULT 0,
    deadline       DATE,
    account_id     UUID REFERENCES accounts(id) ON DELETE SET NULL,
    is_completed   BOOLEAN NOT NULL DEFAULT FALSE,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------- TRANSACOES RECORRENTES ----------
CREATE TABLE IF NOT EXISTS recurring_transactions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_id  UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    type        transaction_type NOT NULL,
    amount      NUMERIC(14,2) NOT NULL CHECK (amount > 0),
    description VARCHAR(255) NOT NULL,
    frequency   VARCHAR(10) NOT NULL CHECK (frequency IN ('weekly','monthly','yearly')),
    day_of_month SMALLINT CHECK (day_of_month BETWEEN 1 AND 31),
    starts_on   DATE NOT NULL,
    ends_on     DATE,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE
);

-- ---------- BALANCE SNAPSHOTS ----------
CREATE TABLE IF NOT EXISTS balance_snapshots (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id  UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    balance     NUMERIC(14,2) NOT NULL,
    snapshot_on DATE NOT NULL,
    source      VARCHAR(20) NOT NULL DEFAULT 'import',
    UNIQUE (account_id, snapshot_on)
);

-- ---------- USER SETTINGS ----------
CREATE TABLE IF NOT EXISTS user_settings (
    user_id  UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    settings JSONB NOT NULL DEFAULT '{}'
);

-- =====================================================================
-- MODULO DE INVESTIMENTOS
-- =====================================================================

DO $$ BEGIN
    CREATE TYPE investment_type AS ENUM
        ('savings','cdb','lci_lca','treasury','fund','stock','fii','etf','crypto','pension','other');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE rate_type AS ENUM
        ('prefixed','cdi_percent','selic','ipca_plus','savings','variable');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE tax_regime AS ENUM ('ir_regressive','exempt','none');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE investment_tx_type AS ENUM ('deposit','withdrawal','yield','dividend','fee','tax');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE contribution_frequency AS ENUM ('once','daily','weekly','monthly','yearly');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ---------- INVESTIMENTOS ----------
CREATE TABLE IF NOT EXISTS investments (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_id    UUID REFERENCES accounts(id) ON DELETE SET NULL,
    name          VARCHAR(120) NOT NULL,
    type          investment_type NOT NULL,
    ticker        VARCHAR(20),
    rate_type     rate_type NOT NULL DEFAULT 'prefixed',
    rate_value    NUMERIC(8,4),
    tax_regime    tax_regime NOT NULL DEFAULT 'ir_regressive',
    started_on    DATE NOT NULL,
    matures_on    DATE,
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    metadata      JSONB NOT NULL DEFAULT '{}',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_investments_user ON investments(user_id);

-- ---------- MOVIMENTACOES DE INVESTIMENTOS ----------
CREATE TABLE IF NOT EXISTS investment_transactions (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investment_id  UUID NOT NULL REFERENCES investments(id) ON DELETE CASCADE,
    type           investment_tx_type NOT NULL,
    amount         NUMERIC(14,2) NOT NULL CHECK (amount > 0),
    occurred_on    DATE NOT NULL,
    quantity       NUMERIC(18,8),
    unit_price     NUMERIC(14,4),
    transaction_id UUID REFERENCES transactions(id) ON DELETE SET NULL,
    notes          TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_inv_tx_inv_date ON investment_transactions(investment_id, occurred_on);

-- ---------- VALOR ATUAL (SNAPSHOTS) ----------
CREATE TABLE IF NOT EXISTS investment_valuations (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investment_id UUID NOT NULL REFERENCES investments(id) ON DELETE CASCADE,
    value         NUMERIC(14,2) NOT NULL,
    valued_on     DATE NOT NULL,
    source        VARCHAR(20) NOT NULL DEFAULT 'manual',
    UNIQUE (investment_id, valued_on)
);

-- ---------- INDICES ECONOMICOS ----------
CREATE TABLE IF NOT EXISTS economic_indices (
    code         VARCHAR(20) NOT NULL,
    reference_on DATE NOT NULL,
    annual_rate  NUMERIC(8,4) NOT NULL,
    PRIMARY KEY (code, reference_on)
);

-- ---------- SIMULACOES SALVAS ----------
CREATE TABLE IF NOT EXISTS simulations (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    investment_id  UUID REFERENCES investments(id) ON DELETE CASCADE,
    name           VARCHAR(120) NOT NULL,
    target_date    DATE NOT NULL,
    annual_rate    NUMERIC(8,4),
    initial_amount NUMERIC(14,2),
    tax_regime     tax_regime NOT NULL DEFAULT 'ir_regressive',
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------- APORTES DA SIMULACAO ----------
CREATE TABLE IF NOT EXISTS simulation_contributions (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_id UUID NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    amount        NUMERIC(14,2) NOT NULL CHECK (amount > 0),
    frequency     contribution_frequency NOT NULL,
    starts_on     DATE NOT NULL,
    ends_on       DATE
);

-- =====================================================================
-- VIEWS
-- =====================================================================

CREATE OR REPLACE VIEW v_account_balances AS
SELECT
    a.id AS account_id,
    a.user_id,
    a.name,
    a.include_in_total,
    a.initial_balance
      + COALESCE(SUM(CASE WHEN t.type = 'income' THEN t.amount
                          WHEN t.type = 'expense' THEN -t.amount END), 0) AS balance
FROM accounts a
LEFT JOIN transactions t ON t.account_id = a.id
WHERE a.is_active
GROUP BY a.id;

CREATE OR REPLACE VIEW v_user_total_balance AS
SELECT user_id, SUM(balance) AS total_balance
FROM v_account_balances
WHERE include_in_total
GROUP BY user_id;

CREATE OR REPLACE VIEW v_monthly_spending_by_account AS
SELECT
    t.user_id,
    t.account_id,
    date_trunc('month', t.occurred_on)::date AS month,
    SUM(t.amount) AS total_spent
FROM transactions t
WHERE t.type = 'expense' AND t.transfer_group_id IS NULL
GROUP BY t.user_id, t.account_id, date_trunc('month', t.occurred_on);

CREATE OR REPLACE VIEW v_monthly_spending_by_category AS
SELECT
    t.user_id,
    t.category_id,
    date_trunc('month', t.occurred_on)::date AS month,
    SUM(t.amount) AS total_spent
FROM transactions t
WHERE t.type = 'expense' AND t.transfer_group_id IS NULL
GROUP BY t.user_id, t.category_id, date_trunc('month', t.occurred_on);

CREATE OR REPLACE VIEW v_budget_status AS
SELECT
    b.user_id,
    b.category_id,
    b.period_month,
    b.amount_limit,
    COALESCE(s.total_spent, 0)                   AS spent,
    b.amount_limit - COALESCE(s.total_spent, 0)  AS remaining
FROM budgets b
LEFT JOIN v_monthly_spending_by_category s
       ON s.user_id = b.user_id
      AND s.category_id = b.category_id
      AND s.month = b.period_month;

CREATE OR REPLACE VIEW v_investment_positions AS
SELECT
    i.id AS investment_id,
    i.user_id,
    i.name,
    i.type,
    COALESCE(SUM(CASE WHEN t.type = 'deposit'    THEN t.amount END), 0)
  - COALESCE(SUM(CASE WHEN t.type = 'withdrawal' THEN t.amount END), 0) AS invested,
    COALESCE(v.value, 0) AS current_value,
    v.valued_on
FROM investments i
LEFT JOIN investment_transactions t ON t.investment_id = i.id
LEFT JOIN LATERAL (
    SELECT value, valued_on FROM investment_valuations
    WHERE investment_id = i.id ORDER BY valued_on DESC LIMIT 1
) v ON TRUE
WHERE i.is_active
GROUP BY i.id, v.value, v.valued_on;

CREATE OR REPLACE VIEW v_user_investment_totals AS
SELECT
    user_id,
    SUM(invested)      AS total_invested,
    SUM(current_value) AS total_current_value,
    SUM(current_value) - SUM(invested) AS total_gain
FROM v_investment_positions
GROUP BY user_id;

-- =====================================================================
-- DADOS INICIAIS
-- =====================================================================
INSERT INTO institutions (code, name, bank_code, parser_key) VALUES
    ('itau',   'Itau',   '341', 'itau'),
    ('picpay', 'PicPay', '380', 'picpay'),
    ('nubank', 'Nubank', '260', 'nubank'),
    ('manual', 'Dinheiro / Manual', NULL, NULL)
ON CONFLICT (code) DO NOTHING;

INSERT INTO categories (name, type)
SELECT name, type::transaction_type
FROM (VALUES
    ('Alimentacao', 'expense'), ('Transporte', 'expense'), ('Moradia', 'expense'),
    ('Lazer', 'expense'), ('Saude', 'expense'), ('Educacao', 'expense'),
    ('Assinaturas', 'expense'), ('Compras', 'expense'),
    ('Salario', 'income'), ('Investimentos', 'income'), ('Outros', 'expense')
) AS c(name, type)
WHERE NOT EXISTS (
    SELECT 1 FROM categories WHERE categories.name = c.name AND categories.user_id IS NULL
);
