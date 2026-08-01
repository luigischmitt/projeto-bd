-- Stored procedures da Etapa 2 (requisito 1)
-- Preenchido na issue #4. O arquivo já existe e é montado no docker-entrypoint-initdb.d
-- para fixar a ordem de carga: schema → procedures → triggers → views → seed.

-- ============================================================================
-- sp_registrar_atendimento_completo
--
-- Insere o atendimento e, em seguida, cada procedimento_realizado descrito em
-- p_procedimentos (um array JSONB). Retorna o id_atendimento criado.
--
-- Atomicidade: todo o corpo da função roda dentro do bloco BEGIN/EXCEPTION.
-- Um bloco PL/pgSQL com cláusula EXCEPTION cria implicitamente um savepoint no
-- seu início; se qualquer INSERT do laço falhar, o runtime desfaz tudo desde
-- esse savepoint — incluindo o INSERT do atendimento já confirmado dentro do
-- bloco — antes de cair no handler. Não é preciso SAVEPOINT/ROLLBACK manual.
--
-- Formato de cada elemento de p_procedimentos:
--   {"id_procedimento": 1, "quantidade": 2, "tempo_real_minutos": 30,
--    "data_hora_inicio": "2026-06-01T08:15:00", "observacao": null}
-- ============================================================================
CREATE OR REPLACE FUNCTION sp_registrar_atendimento_completo(
    p_data_hora        TIMESTAMP,
    p_duracao_minutos  INTEGER,
    p_id_paciente      INTEGER,
    p_id_residente     INTEGER,
    p_id_preceptor     INTEGER,
    p_id_unidade       INTEGER,
    p_procedimentos    JSONB
) RETURNS INTEGER AS $$
DECLARE
    v_id_atendimento  INTEGER;
    v_procedimento    JSONB;
BEGIN
    INSERT INTO atendimento (
        data_hora, duracao_minutos, id_paciente, id_residente, id_preceptor, id_unidade
    ) VALUES (
        p_data_hora, p_duracao_minutos, p_id_paciente, p_id_residente, p_id_preceptor, p_id_unidade
    )
    RETURNING id_atendimento INTO v_id_atendimento;

    FOR v_procedimento IN SELECT * FROM jsonb_array_elements(p_procedimentos)
    LOOP
        INSERT INTO procedimento_realizado (
            id_atendimento, id_procedimento, quantidade, tempo_real_minutos,
            data_hora_inicio, observacao
        ) VALUES (
            v_id_atendimento,
            (v_procedimento->>'id_procedimento')::INTEGER,
            (v_procedimento->>'quantidade')::INTEGER,
            (v_procedimento->>'tempo_real_minutos')::INTEGER,
            (v_procedimento->>'data_hora_inicio')::TIMESTAMP,
            v_procedimento->>'observacao'
        );
    END LOOP;

    RETURN v_id_atendimento;
EXCEPTION
    WHEN foreign_key_violation THEN
        RAISE EXCEPTION 'Referência inválida ao registrar atendimento (paciente, residente, preceptor, unidade ou procedimento inexistente): %', SQLERRM;
    WHEN check_violation THEN
        RAISE EXCEPTION 'Dado inválido ao registrar atendimento (violação de regra de integridade): %', SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- sp_calcular_tempo_medio_espera
--
-- Para cada unidade, calcula a média do tempo de espera dos pacientes: a
-- diferença entre a chegada (atendimento.data_hora) e o início do primeiro
-- procedimento realizado naquele atendimento (MIN(data_hora_inicio)).
-- Atendimentos sem nenhum procedimento com data_hora_inicio preenchida ficam
-- fora do cálculo (o INNER JOIN com a subconsulta já garante isso).
-- ============================================================================
CREATE OR REPLACE FUNCTION sp_calcular_tempo_medio_espera()
RETURNS TABLE (
    id_unidade                    INTEGER,
    nome_unidade                  VARCHAR,
    tempo_medio_espera_minutos    NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        u.id_unidade,
        u.nome,
        ROUND(AVG(EXTRACT(EPOCH FROM (inicio.data_hora_inicio_min - a.data_hora)) / 60)::NUMERIC, 2)
    FROM atendimento a
    JOIN unidade u ON u.id_unidade = a.id_unidade
    JOIN (
        SELECT id_atendimento, MIN(data_hora_inicio) AS data_hora_inicio_min
        FROM procedimento_realizado
        WHERE data_hora_inicio IS NOT NULL
        GROUP BY id_atendimento
    ) inicio ON inicio.id_atendimento = a.id_atendimento
    GROUP BY u.id_unidade, u.nome
    ORDER BY u.id_unidade;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- sp_reajustar_escala
--
-- Move todas as escalas do residente do dia/turno de origem para o dia/turno
-- de destino. Antes de alterar qualquer linha, verifica se o residente já
-- está escalado no destino (em qualquer unidade); se estiver, aborta com
-- RAISE EXCEPTION sem tocar na tabela.
-- ============================================================================
CREATE OR REPLACE PROCEDURE sp_reajustar_escala(
    p_id_residente   INTEGER,
    p_dia_origem     VARCHAR,
    p_turno_origem   VARCHAR,
    p_dia_destino    VARCHAR,
    p_turno_destino  VARCHAR
) AS $$
DECLARE
    v_qtd_conflitos  INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_qtd_conflitos
    FROM escala
    WHERE id_residente = p_id_residente
      AND dia_semana = p_dia_destino
      AND turno = p_turno_destino;

    IF v_qtd_conflitos > 0 THEN
        RAISE EXCEPTION 'Residente % já possui escala em %/% (destino ocupado)',
            p_id_residente, p_dia_destino, p_turno_destino;
    END IF;

    UPDATE escala
    SET dia_semana = p_dia_destino,
        turno = p_turno_destino
    WHERE id_residente = p_id_residente
      AND dia_semana = p_dia_origem
      AND turno = p_turno_origem;
END;
$$ LANGUAGE plpgsql;
