-- Consultas analíticas Etapa 1 (req. 4) — referência para P2 / demonstração no psql
-- Pré-requisito: 01_schema.sql + 02_seed.sql

-- Consulta 1: Ranking dos residentes por número de atendimentos (nome + total)
SELECT p.nome AS residente, COUNT(a.id_atendimento) AS total_atendimentos
FROM residente r
JOIN pessoa p ON p.id_pessoa = r.id_profissional
JOIN atendimento a ON a.id_residente = r.id_profissional
GROUP BY r.id_profissional, p.nome
ORDER BY total_atendimentos DESC, p.nome;

-- Consulta 2: Preceptores com mais de 5 atendimentos supervisionados em um mês
-- Exemplo: junho/2026 (seed: Ana Preceptora id=6 tem 6 supervisões)
SELECT p.nome AS preceptor, COUNT(a.id_atendimento) AS total_supervisoes
FROM preceptor pr
JOIN pessoa p ON p.id_pessoa = pr.id_profissional
JOIN atendimento a ON a.id_preceptor = pr.id_profissional
WHERE a.data_hora >= DATE '2026-06-01'
  AND a.data_hora <  DATE '2026-07-01'
GROUP BY pr.id_profissional, p.nome
HAVING COUNT(a.id_atendimento) > 5
ORDER BY total_supervisoes DESC;

-- Consulta 3: Por unidade, quantidade de plantões escalados por residente
-- Nota: escala não tem data de calendário; "mês corrente" = escalas vigentes no sistema
SELECT u.nome AS unidade,
       p.nome AS residente,
       COUNT(e.id_escala) AS plantaoes
FROM escala e
JOIN unidade u ON u.id_unidade = e.id_unidade
JOIN pessoa p ON p.id_pessoa = e.id_residente
GROUP BY u.id_unidade, u.nome, e.id_residente, p.nome
ORDER BY u.nome, plantaoes DESC, p.nome;

-- Consulta 4: Pacientes que nunca realizaram procedimento de nivel_risco ALTO
SELECT p.id_pessoa, p.nome
FROM paciente pac
JOIN pessoa p ON p.id_pessoa = pac.id_pessoa
WHERE NOT EXISTS (
    SELECT 1
    FROM atendimento a
    JOIN procedimento_realizado pr ON pr.id_atendimento = a.id_atendimento
    JOIN procedimento proc ON proc.id_procedimento = pr.id_procedimento
    WHERE a.id_paciente = pac.id_pessoa
      AND proc.nivel_risco = 'ALTO'
)
ORDER BY p.nome;
