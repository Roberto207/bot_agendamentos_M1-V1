-- 1️⃣ Criar tipos ENUM antes de usá-los
-- CREATE TYPE status_agendamento AS ENUM ('confirmado', 'cancelado');

-- CREATE TYPE tipo_servico AS ENUM (
--     'corte_cabelo',
--     'manicure',
--     'barba',
--     'maquiagem'
-- );

-- 1️⃣ Adicionar o valor 'corte_cabelo' no ENUM, se ainda não existir
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM pg_enum e
        JOIN pg_type t ON t.oid = e.enumtypid
        WHERE t.typname = 'tipo_servico' AND e.enumlabel = 'corte_cabelo'
    ) THEN
        ALTER TYPE tipo_servico ADD VALUE 'corte_cabelo';
    END IF;
    IF NOT EXISTS (
        SELECT 1 
        FROM pg_enum e
        JOIN pg_type t ON t.oid = e.enumtypid
        WHERE t.typname = 'tipo_servico' AND e.enumlabel = 'barba'
    ) THEN
        ALTER TYPE tipo_servico ADD VALUE 'barba';
    END IF;
END;
$$;

alter type tipo_servico add value if not exists 'manicure';
alter type tipo_servico add value if not exists 'maquiagem';


-- 2️⃣ Criar tabela de agendamentos
CREATE TABLE IF NOT EXISTS agendamentos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    telefone VARCHAR(20) NOT NULL,
    data_servico DATE NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fim TIME NOT NULL,
    status status_agendamento DEFAULT 'confirmado' NOT NULL,
    tipos_servico tipo_servico,
    criado_em TIMESTAMP DEFAULT NOW() NOT NULL
);

-- 3️⃣ Criar extensão para constraints de exclusão (opcional)
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- 4️⃣ Função para verificar sobreposição de horários
CREATE OR REPLACE FUNCTION verificar_sobreposicao()
RETURNS TRIGGER AS $$
DECLARE
    conflito RECORD;
BEGIN
    SELECT hora_inicio, hora_fim
    INTO conflito
    FROM agendamentos
    WHERE data_servico = NEW.data_servico
      AND status = 'confirmado'
      AND id <> COALESCE(NEW.id, -1)
      AND NEW.hora_inicio < hora_fim
      AND NEW.hora_fim > hora_inicio
    LIMIT 1;

    IF FOUND THEN
        RAISE EXCEPTION 
        'Já existe um agendamento das % às % nesta data.',
        to_char(conflito.hora_inicio, 'HH24:MI'),
        to_char(conflito.hora_fim, 'HH24:MI');
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 5️⃣ Triggers para checar sobreposição antes de INSERT e UPDATE
CREATE OR REPLACE TRIGGER trigger_verificar_sobreposicao_insert
BEFORE INSERT ON agendamentos
FOR EACH ROW
EXECUTE FUNCTION verificar_sobreposicao();

CREATE OR REPLACE TRIGGER trigger_verificar_sobreposicao_update
BEFORE UPDATE ON agendamentos
FOR EACH ROW
EXECUTE FUNCTION verificar_sobreposicao();

-- 6️⃣ Função para listar horários disponíveis
CREATE OR REPLACE FUNCTION horarios_disponiveis(p_data DATE)
RETURNS TABLE(horario TIME) AS $$
BEGIN
    RETURN QUERY
    SELECT (h)::time
    FROM generate_series(
        p_data + TIME '08:00',
        p_data + TIME '17:00',
        INTERVAL '1 hour'
    ) AS h
    WHERE NOT EXISTS (
        SELECT 1
        FROM agendamentos a
        WHERE a.data_servico = p_data
          AND a.status = 'confirmado'
          AND (h::time) < a.hora_fim
          AND ((h + INTERVAL '1 hour')::time) > a.hora_inicio
    );
END;
$$ LANGUAGE plpgsql;

-- 7️⃣ Inserir valor padrão em tipos_servico para registros existentes (opcional)
UPDATE agendamentos
SET tipos_servico = 'corte_cabelo'
WHERE tipos_servico IS NULL;

-- 8️⃣ Consultas de teste
-- Todos os agendamentos
SELECT * FROM agendamentos;

-- Horários disponíveis em uma data específica
SELECT * FROM horarios_disponiveis('2026-07-01');

-- 9️⃣ Exemplo de inserção
-- INSERT INTO agendamentos (nome, telefone, data_servico, hora_inicio, hora_fim, tipos_servico)
-- VALUES ('Roberto', '11987654321', '2026-08-01', '11:30', '12:30', 'barba');

