-- Triggers da Etapa 2 (requisito 2)
-- Carregado antes do seed de propósito: assim o banco sobe com
-- procedimento.media_tempo_procedimento já calculada e com linhas em auditoria_atendimento.

-- =============================================================================
-- trg_check_sobreposicao_escala — BEFORE INSERT OR UPDATE em escala
-- =============================================================================
-- Divisão de responsabilidade com a constraint declarativa:
--   uq_escala_unidade_dia_turno_residente (UNIQUE em id_unidade, dia_semana, turno,
--   id_residente) já impede o mesmo residente duas vezes no mesmo dia/turno DENTRO da
--   MESMA unidade — isso é escopo da UNIQUE, e a trigger não reimplementa essa checagem.
--   O que a UNIQUE não alcança é o residente escalado no mesmo dia/turno em UNIDADES
--   DIFERENTES (linhas com id_unidade distinto não colidem na UNIQUE composta). É
--   exatamente esse buraco que a trigger cobre.
CREATE OR REPLACE FUNCTION fn_check_sobreposicao_escala()
RETURNS TRIGGER AS $$
DECLARE
    v_conflito INTEGER;
BEGIN
    SELECT id_escala INTO v_conflito
    FROM escala
    WHERE id_residente = NEW.id_residente
      AND dia_semana = NEW.dia_semana
      AND turno = NEW.turno
      AND id_unidade <> NEW.id_unidade
      -- No UPDATE, a própria linha sendo atualizada não pode contar como conflito
      -- consigo mesma (senão um UPDATE que não muda dia/turno se rejeitaria sozinho).
      AND id_escala <> NEW.id_escala
    LIMIT 1;

    IF v_conflito IS NOT NULL THEN
        RAISE EXCEPTION
            'Residente % já está escalado no dia % turno % em outra unidade (id_escala=%)',
            NEW.id_residente, NEW.dia_semana, NEW.turno, v_conflito;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_sobreposicao_escala
    BEFORE INSERT OR UPDATE ON escala
    FOR EACH ROW
    EXECUTE FUNCTION fn_check_sobreposicao_escala();

-- =============================================================================
-- trg_audita_atendimento — AFTER INSERT OR UPDATE OR DELETE em atendimento
-- =============================================================================
CREATE OR REPLACE FUNCTION fn_audita_atendimento()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO auditoria_atendimento (id_atendimento, operacao, usuario, dados_antigos, dados_novos)
        VALUES (NEW.id_atendimento, 'INSERT', current_user, NULL, to_jsonb(NEW));
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO auditoria_atendimento (id_atendimento, operacao, usuario, dados_antigos, dados_novos)
        VALUES (NEW.id_atendimento, 'UPDATE', current_user, to_jsonb(OLD), to_jsonb(NEW));
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO auditoria_atendimento (id_atendimento, operacao, usuario, dados_antigos, dados_novos)
        VALUES (OLD.id_atendimento, 'DELETE', current_user, to_jsonb(OLD), NULL);
    END IF;

    RETURN NULL; -- trigger AFTER: valor de retorno é ignorado
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audita_atendimento
    AFTER INSERT OR UPDATE OR DELETE ON atendimento
    FOR EACH ROW
    EXECUTE FUNCTION fn_audita_atendimento();

-- =============================================================================
-- trg_atualiza_media_procedimentos — AFTER INSERT em procedimento_realizado
-- =============================================================================
CREATE OR REPLACE FUNCTION fn_atualiza_media_procedimentos()
RETURNS TRIGGER AS $$
DECLARE
    v_id_procedimento INTEGER;
BEGIN
    v_id_procedimento := COALESCE(NEW.id_procedimento, OLD.id_procedimento);

    UPDATE procedimento
    SET media_tempo_procedimento = (
        SELECT AVG(tempo_real_minutos)
        FROM procedimento_realizado
        WHERE id_procedimento = v_id_procedimento
    )
    WHERE id_procedimento = v_id_procedimento;

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_atualiza_media_procedimentos ON procedimento_realizado;

CREATE TRIGGER trg_atualiza_media_procedimentos
    AFTER INSERT OR UPDATE OR DELETE ON procedimento_realizado
    FOR EACH ROW
    EXECUTE FUNCTION fn_atualiza_media_procedimentos();
