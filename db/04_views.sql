-- Views da Etapa 2 (requisito 3)
-- Preenchido na issue #6.

-- vw_pacientes_internados
-- Internação "em curso" é a mais recente (maior data_hora_entrada) de cada paciente
-- com data_hora_saida IS NULL. Um paciente que teve alta e voltou a internar aparece;
-- um que internou e depois teve alta some da view, mesmo que uma internação mais antiga
-- ainda esteja em aberto (a mais recente sempre decide).
-- O ORDER BY do DISTINCT ON casa com o índice ix_internacao_em_curso
-- (id_paciente, data_hora_entrada DESC).
CREATE VIEW vw_pacientes_internados AS
SELECT
    ultima.id_internacao,
    ultima.id_paciente,
    pe.nome AS nome_paciente,
    ultima.id_unidade,
    u.nome AS nome_unidade,
    ultima.data_hora_entrada,
    (now() - ultima.data_hora_entrada) AS tempo_internado
FROM (
    SELECT DISTINCT ON (id_paciente) *
    FROM internacao
    ORDER BY id_paciente, data_hora_entrada DESC
) ultima
JOIN pessoa pe ON pe.id_pessoa = ultima.id_paciente
JOIN unidade u ON u.id_unidade = ultima.id_unidade
WHERE ultima.data_hora_saida IS NULL;

-- vw_residentes_sem_supervisor
-- Uma linha por escala ativa cujo preceptor responsável não tem titulação de doutor
-- (fora de {DOUTOR, POS_DOUTOR}). Um mesmo residente pode aparecer mais de uma vez se
-- estiver escalado em mais de um dia/turno sem supervisão de doutor.
CREATE VIEW vw_residentes_sem_supervisor AS
SELECT
    e.id_escala,
    r.id_profissional AS id_residente,
    pr.nome AS nome_residente,
    e.id_unidade,
    u.nome AS nome_unidade,
    e.dia_semana,
    e.turno,
    p.id_profissional AS id_preceptor,
    pp.nome AS nome_preceptor,
    p.titulacao AS titulacao_preceptor
FROM escala e
JOIN residente r ON r.id_profissional = e.id_residente
JOIN pessoa pr ON pr.id_pessoa = r.id_profissional
JOIN preceptor p ON p.id_profissional = e.id_preceptor
JOIN pessoa pp ON pp.id_pessoa = p.id_profissional
JOIN unidade u ON u.id_unidade = e.id_unidade
WHERE p.titulacao NOT IN ('DOUTOR', 'POS_DOUTOR');

-- vw_estatisticas_atendimentos_mensal
-- Uma linha por mês (date_trunc('month', data_hora)) e unidade, com total de
-- atendimentos, duração média e os 3 procedimentos mais frequentes do período
-- (por soma de quantidade realizada), como um array JSON ordenado do mais para o
-- menos frequente. Meses/unidades sem nenhum procedimento registrado retornam '[]'.
CREATE VIEW vw_estatisticas_atendimentos_mensal AS
WITH resumo AS (
    SELECT
        date_trunc('month', a.data_hora) AS mes,
        a.id_unidade,
        COUNT(*) AS total_atendimentos,
        AVG(a.duracao_minutos) AS duracao_media_minutos
    FROM atendimento a
    GROUP BY date_trunc('month', a.data_hora), a.id_unidade
),
procedimentos_mes AS (
    SELECT
        date_trunc('month', a.data_hora) AS mes,
        a.id_unidade,
        proc.nome AS nome_procedimento,
        SUM(pr.quantidade) AS quantidade_realizada,
        ROW_NUMBER() OVER (
            PARTITION BY date_trunc('month', a.data_hora), a.id_unidade
            ORDER BY SUM(pr.quantidade) DESC, proc.nome
        ) AS posicao
    FROM atendimento a
    JOIN procedimento_realizado pr ON pr.id_atendimento = a.id_atendimento
    JOIN procedimento proc ON proc.id_procedimento = pr.id_procedimento
    GROUP BY date_trunc('month', a.data_hora), a.id_unidade, proc.id_procedimento, proc.nome
),
procedimentos_top AS (
    SELECT
        mes,
        id_unidade,
        json_agg(
            json_build_object('procedimento', nome_procedimento, 'quantidade', quantidade_realizada)
            ORDER BY quantidade_realizada DESC, nome_procedimento
        ) AS procedimentos_mais_frequentes
    FROM procedimentos_mes
    WHERE posicao <= 3
    GROUP BY mes, id_unidade
)
SELECT
    r.mes,
    r.id_unidade,
    u.nome AS nome_unidade,
    r.total_atendimentos,
    r.duracao_media_minutos,
    COALESCE(pt.procedimentos_mais_frequentes, '[]'::json) AS procedimentos_mais_frequentes
FROM resumo r
JOIN unidade u ON u.id_unidade = r.id_unidade
LEFT JOIN procedimentos_top pt ON pt.mes = r.mes AND pt.id_unidade = r.id_unidade
ORDER BY r.mes, r.id_unidade;
