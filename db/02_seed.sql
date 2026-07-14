-- Seed Etapa 1 — mínimos do enunciado + cenários das consultas analíticas
-- Requer: db/01_schema.sql já aplicado
-- Cenário consulta 2: preceptor id=6 (Ana Preceptora) com >5 atendimentos em 2026-06
-- Cenário consulta 4: paciente id=5 (Pedro SemRiscoAlto) sem procedimento ALTO

-- Pessoas: 5 pacientes (1-5) + 5 preceptores (6-10) + 5 residentes (11-15)
INSERT INTO pessoa (id_pessoa, nome, cpf, data_nascimento, is_flamengo, telefone) VALUES
(1,  'Carlos Paciente',      '11111111111', '1990-01-10', TRUE,  '83990000001'),
(2,  'Maria Paciente',       '22222222222', '1985-03-15', FALSE, '83990000002'),
(3,  'Joao Paciente',        '33333333333', '1992-07-20', TRUE,  '83990000003'),
(4,  'Lucia Paciente',       '44444444444', '1978-11-05', FALSE, '83990000004'),
(5,  'Pedro SemRiscoAlto',   '55555555555', '2000-05-30', FALSE, '83990000005'),
(6,  'Ana Preceptora',       '66666666666', '1975-02-12', FALSE, '83990000006'),
(7,  'Bruno Preceptor',      '77777777777', '1970-08-22', TRUE,  '83990000007'),
(8,  'Clara Preceptora',     '88888888888', '1980-04-18', FALSE, '83990000008'),
(9,  'Diego Preceptor',      '99999999999', '1972-09-09', FALSE, '83990000009'),
(10, 'Elena Preceptora',     '10101010101', '1977-12-01', TRUE,  '83990000010'),
(11, 'Felipe Residente',     '12121212121', '1995-01-01', TRUE,  '83990000011'),
(12, 'Gabriela Residente',   '13131313131', '1996-02-02', FALSE, '83990000012'),
(13, 'Hugo Residente',       '14141414141', '1994-03-03', FALSE, '83990000013'),
(14, 'Iris Residente',       '15151515151', '1997-04-04', TRUE,  '83990000014'),
(15, 'Jonas Residente',      '16161616161', '1993-05-05', FALSE, '83990000015');

SELECT setval('pessoa_id_pessoa_seq', 15);

INSERT INTO paciente (id_pessoa, num_convenio, alergias, grupo_sanguineo) VALUES
(1, 'CONV-001', 'Penicilina', 'A+'),
(2, 'CONV-002', NULL, 'O-'),
(3, 'CONV-003', 'Dipirona', 'B+'),
(4, 'CONV-004', NULL, 'AB+'),
(5, 'CONV-005', 'Nenhuma', 'O+');

INSERT INTO profissional (id_pessoa, crm, data_admissao, especialidade) VALUES
(6,  'CRM-PB-1001', '2010-01-15', 'Clinica Medica'),
(7,  'CRM-PB-1002', '2008-03-20', 'Cirurgia'),
(8,  'CRM-PB-1003', '2012-06-10', 'Pediatria'),
(9,  'CRM-PB-1004', '2005-09-01', 'Cardiologia'),
(10, 'CRM-PB-1005', '2015-11-11', 'Ortopedia'),
(11, 'CRM-PB-2001', '2023-02-01', 'Clinica Medica'),
(12, 'CRM-PB-2002', '2024-02-01', 'Cirurgia'),
(13, 'CRM-PB-2003', '2022-02-01', 'Pediatria'),
(14, 'CRM-PB-2004', '2025-02-01', 'Cardiologia'),
(15, 'CRM-PB-2005', '2023-08-01', 'Ortopedia');

INSERT INTO preceptor (id_profissional, titulacao) VALUES
(6, 'Doutor'),
(7, 'Mestre'),
(8, 'Doutor'),
(9, 'Especialista'),
(10, 'Mestre');

INSERT INTO residente (id_profissional, ano_residencia) VALUES
(11, 'R1'),
(12, 'R2'),
(13, 'R3'),
(14, 'R1'),
(15, 'R2');

INSERT INTO unidade (id_unidade, nome, tipo, capacidade_leitos) VALUES
(1, 'Enfermaria Norte', 'ENFERMARIA', 30),
(2, 'UTI Central', 'UTI', 12),
(3, 'Pronto-Socorro', 'PRONTO_SOCORRO', 20);

SELECT setval('unidade_id_unidade_seq', 3);

INSERT INTO procedimento (id_procedimento, codigo, nome, tempo_medio_minutos, nivel_risco) VALUES
(1, 'PROC-01', 'Coleta de sangue', 10, 'BAIXO'),
(2, 'PROC-02', 'Aplicacao de medicacao', 15, 'BAIXO'),
(3, 'PROC-03', 'Sutura simples', 30, 'MEDIO'),
(4, 'PROC-04', 'Punção lombar', 45, 'ALTO'),
(5, 'PROC-05', 'Intubacao', 20, 'ALTO');

SELECT setval('procedimento_id_procedimento_seq', 5);

-- 10 atendimentos: 6 em 2026-06 para Ana (id_preceptor=6) superar 5 supervisões
INSERT INTO atendimento (id_atendimento, data_hora, duracao_minutos, id_paciente, id_residente, id_preceptor) VALUES
(1,  '2026-06-02 08:00:00', 40, 1, 11, 6),
(2,  '2026-06-03 09:00:00', 35, 2, 11, 6),
(3,  '2026-06-04 10:00:00', 50, 3, 12, 6),
(4,  '2026-06-05 11:00:00', 45, 4, 12, 6),
(5,  '2026-06-06 14:00:00', 60, 1, 13, 6),
(6,  '2026-06-07 15:00:00', 30, 2, 13, 6),
(7,  '2026-06-10 08:30:00', 55, 3, 14, 7),
(8,  '2026-05-12 09:30:00', 40, 4, 15, 8),
(9,  '2026-05-15 10:30:00', 25, 5, 11, 9),
(10, '2026-05-20 16:00:00', 70, 5, 12, 10);

SELECT setval('atendimento_id_atendimento_seq', 10);

-- 10 procedimentos realizados; paciente 5 só BAIXO/MEDIO; mistura faturado
INSERT INTO procedimento_realizado (id_atendimento, id_procedimento, quantidade, tempo_real_minutos, observacao, faturado) VALUES
(1,  1, 1, 12, NULL, FALSE),
(1,  3, 1, 28, 'Sem intercorrencia', TRUE),
(2,  2, 2, 18, NULL, FALSE),
(3,  4, 1, 50, 'Paciente ansioso', FALSE),
(4,  5, 1, 22, NULL, TRUE),
(5,  1, 1, 11, NULL, FALSE),
(6,  3, 1, 35, NULL, FALSE),
(7,  4, 1, 48, NULL, FALSE),
(9,  1, 1, 10, 'Paciente 5 - so baixo', FALSE),
(10, 3, 1, 32, 'Paciente 5 - medio', FALSE);

-- Escalas atuais (consulta 3: plantões por unidade/residente; sem data de calendário na tabela)
INSERT INTO escala (id_escala, id_unidade, dia_semana, turno, id_residente, id_preceptor) VALUES
(1, 1, 'SEG', 'MANHA', 11, 6),
(2, 1, 'SEG', 'TARDE', 12, 6),
(3, 1, 'TER', 'MANHA', 11, 7),
(4, 2, 'SEG', 'NOITE', 13, 8),
(5, 2, 'QUA', 'MANHA', 14, 9),
(6, 3, 'SEX', 'TARDE', 15, 10),
(7, 3, 'SEX', 'NOITE', 11, 6);

SELECT setval('escala_id_escala_seq', 7);
