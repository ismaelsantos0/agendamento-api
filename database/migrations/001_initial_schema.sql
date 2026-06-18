-- =============================================================
-- migrations/001_initial_schema.sql
-- Sistema de Agendamento Simplificado
-- =============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================
-- TABELA: users
-- =============================================================
CREATE TABLE IF NOT EXISTS users (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username     VARCHAR(60)   NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role         VARCHAR(20)   NOT NULL DEFAULT 'standard' CHECK (role IN ('master', 'standard')),
    is_active    BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- Apenas UM master permitido
CREATE UNIQUE INDEX IF NOT EXISTS uq_single_master ON users (role) WHERE role = 'master';

-- =============================================================
-- TABELA: services
-- =============================================================
CREATE TABLE IF NOT EXISTS services (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name             VARCHAR(100) NOT NULL,
    duration_minutes INTEGER      NOT NULL CHECK (duration_minutes > 0),
    is_active        BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- =============================================================
-- TABELA: availability_rules
-- Regras gerais da semana (0 = Domingo, 1 = Segunda, etc.)
-- =============================================================
CREATE TABLE IF NOT EXISTS availability_rules (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    start_time  TIME    NOT NULL,
    end_time    TIME    NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_availability_time CHECK (end_time > start_time),
    CONSTRAINT uq_day_of_week UNIQUE (day_of_week)
);

-- =============================================================
-- TABELA: appointments
-- =============================================================
CREATE TABLE IF NOT EXISTS appointments (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_name  VARCHAR(120)  NOT NULL,
    customer_phone VARCHAR(20)   NOT NULL,
    service_id     UUID          NOT NULL REFERENCES services(id),
    start_time     TIMESTAMPTZ   NOT NULL,
    end_time       TIMESTAMPTZ   NOT NULL,
    status         VARCHAR(20)   NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'cancelled', 'completed')),
    notes          TEXT,
    created_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_time_order CHECK (end_time > start_time)
);

CREATE INDEX IF NOT EXISTS idx_appointments_time_range
    ON appointments (start_time, end_time)
    WHERE status NOT IN ('cancelled');

-- =============================================================
-- TRIGGER para updated_at
-- =============================================================
CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
CREATE TRIGGER trg_services_updated_at BEFORE UPDATE ON services FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
CREATE TRIGGER trg_availability_updated_at BEFORE UPDATE ON availability_rules FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
CREATE TRIGGER trg_appointments_updated_at BEFORE UPDATE ON appointments FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
