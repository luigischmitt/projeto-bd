-- Schema Etapa 1 — Gestão Hospitalar Dra. Yuska
-- PostgreSQL — SQL puro

DROP TABLE IF EXISTS procedimento_realizado CASCADE;
DROP TABLE IF EXISTS escala CASCADE;
DROP TABLE IF EXISTS atendimento CASCADE;
DROP TABLE IF EXISTS procedimento CASCADE;
DROP TABLE IF EXISTS unidade CASCADE;
DROP TABLE IF EXISTS preceptor CASCADE;
DROP TABLE IF EXISTS residente CASCADE;
DROP TABLE IF EXISTS profissional CASCADE;
DROP TABLE IF EXISTS paciente CASCADE;
DROP TABLE IF EXISTS pessoa CASCADE;

CREATE TABLE pessoa (
    id_pessoa        SERIAL PRIMARY KEY,
    nome             VARCHAR(120) NOT NULL,
    cpf              CHAR(11) NOT NULL,
    data_nascimento  DATE NOT NULL,
    is_flamengo      BOOLEAN NOT NULL DEFAULT FALSE,
    telefone         VARCHAR(20) NOT NULL,
    CONSTRAINT uq_pessoa_cpf UNIQUE (cpf)
);

CREATE TABLE paciente (
    id_pessoa        INTEGER PRIMARY KEY,
    num_convenio     VARCHAR(40),
    alergias         TEXT,
    grupo_sanguineo  VARCHAR(3),
    CONSTRAINT fk_paciente_pessoa
        FOREIGN KEY (id_pessoa) REFERENCES pessoa (id_pessoa)
);

CREATE TABLE profissional (
    id_pessoa        INTEGER PRIMARY KEY,
    crm              VARCHAR(20) NOT NULL,
    data_admissao    DATE NOT NULL,
    especialidade    VARCHAR(80) NOT NULL,
    CONSTRAINT uq_profissional_crm UNIQUE (crm),
    CONSTRAINT fk_profissional_pessoa
        FOREIGN KEY (id_pessoa) REFERENCES pessoa (id_pessoa)
);

CREATE TABLE preceptor (
    id_profissional  INTEGER PRIMARY KEY,
    titulacao        VARCHAR(60) NOT NULL,
    CONSTRAINT fk_preceptor_profissional
        FOREIGN KEY (id_profissional) REFERENCES profissional (id_pessoa)
);

CREATE TABLE residente (
    id_profissional  INTEGER PRIMARY KEY,
    ano_residencia   VARCHAR(2) NOT NULL,
    CONSTRAINT ck_residente_ano
        CHECK (ano_residencia IN ('R1', 'R2', 'R3')),
    CONSTRAINT fk_residente_profissional
        FOREIGN KEY (id_profissional) REFERENCES profissional (id_pessoa)
);

CREATE TABLE unidade (
    id_unidade         SERIAL PRIMARY KEY,
    nome               VARCHAR(80) NOT NULL,
    tipo               VARCHAR(20) NOT NULL,
    capacidade_leitos  INTEGER NOT NULL,
    CONSTRAINT ck_unidade_tipo
        CHECK (tipo IN ('ENFERMARIA', 'UTI', 'PRONTO_SOCORRO', 'AMBULATORIO')),
    CONSTRAINT ck_unidade_capacidade
        CHECK (capacidade_leitos >= 0)
);

CREATE TABLE procedimento (
    id_procedimento      SERIAL PRIMARY KEY,
    codigo               VARCHAR(20) NOT NULL,
    nome                 VARCHAR(120) NOT NULL,
    tempo_medio_minutos  INTEGER NOT NULL,
    nivel_risco          VARCHAR(5) NOT NULL,
    CONSTRAINT uq_procedimento_codigo UNIQUE (codigo),
    CONSTRAINT ck_procedimento_tempo
        CHECK (tempo_medio_minutos > 0),
    CONSTRAINT ck_procedimento_risco
        CHECK (nivel_risco IN ('BAIXO', 'MEDIO', 'ALTO'))
);

CREATE TABLE atendimento (
    id_atendimento    SERIAL PRIMARY KEY,
    data_hora         TIMESTAMP NOT NULL,
    duracao_minutos   INTEGER NOT NULL,
    id_paciente       INTEGER NOT NULL,
    id_residente      INTEGER NOT NULL,
    id_preceptor      INTEGER NOT NULL,
    CONSTRAINT ck_atendimento_duracao
        CHECK (duracao_minutos > 0),
    CONSTRAINT fk_atendimento_paciente
        FOREIGN KEY (id_paciente) REFERENCES paciente (id_pessoa),
    CONSTRAINT fk_atendimento_residente
        FOREIGN KEY (id_residente) REFERENCES residente (id_profissional),
    CONSTRAINT fk_atendimento_preceptor
        FOREIGN KEY (id_preceptor) REFERENCES preceptor (id_profissional)
);

CREATE TABLE procedimento_realizado (
    id_atendimento       INTEGER NOT NULL,
    id_procedimento      INTEGER NOT NULL,
    quantidade           INTEGER NOT NULL,
    tempo_real_minutos   INTEGER NOT NULL,
    observacao           TEXT,
    faturado             BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_procedimento_realizado
        PRIMARY KEY (id_atendimento, id_procedimento),
    CONSTRAINT ck_pr_quantidade
        CHECK (quantidade > 0),
    CONSTRAINT ck_pr_tempo
        CHECK (tempo_real_minutos > 0),
    CONSTRAINT fk_pr_atendimento
        FOREIGN KEY (id_atendimento) REFERENCES atendimento (id_atendimento),
    CONSTRAINT fk_pr_procedimento
        FOREIGN KEY (id_procedimento) REFERENCES procedimento (id_procedimento)
);

CREATE TABLE escala (
    id_escala         SERIAL PRIMARY KEY,
    id_unidade        INTEGER NOT NULL,
    dia_semana        VARCHAR(3) NOT NULL,
    turno             VARCHAR(5) NOT NULL,
    id_residente      INTEGER NOT NULL,
    id_preceptor      INTEGER NOT NULL,
    CONSTRAINT ck_escala_dia
        CHECK (dia_semana IN ('SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SAB', 'DOM')),
    CONSTRAINT ck_escala_turno
        CHECK (turno IN ('MANHA', 'TARDE', 'NOITE')),
    CONSTRAINT uq_escala_unidade_dia_turno_residente
        UNIQUE (id_unidade, dia_semana, turno, id_residente),
    CONSTRAINT fk_escala_unidade
        FOREIGN KEY (id_unidade) REFERENCES unidade (id_unidade),
    CONSTRAINT fk_escala_residente
        FOREIGN KEY (id_residente) REFERENCES residente (id_profissional),
    CONSTRAINT fk_escala_preceptor
        FOREIGN KEY (id_preceptor) REFERENCES preceptor (id_profissional)
);
