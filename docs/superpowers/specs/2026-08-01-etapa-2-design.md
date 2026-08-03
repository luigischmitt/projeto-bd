# Etapa 2 — Design

Data: 2026-08-01
Projeto: Sistema de Gestão Hospitalar (Dra. Yuska) — `luigischmitt/projeto-bd`

## Objetivo

Adicionar regras de negócio no banco (stored procedures, triggers, views), migrar toda a
camada de persistência da aplicação para uma ORM e demonstrar controle de concorrência
com transações.

## Decisões estruturantes

| Decisão | Escolha | Motivo |
| --- | --- | --- |
| Convivência com a Etapa 1 | **Substituir**. Os repositories em SQL cru são deletados. | A Etapa 1 já foi apresentada ao professor. A tag `etapa-1` preserva o estado entregue. |
| ORM | **SQLAlchemy 2.0 async** sobre o driver `psycopg` já presente. | Recomendada no enunciado, integra com FastAPI/Pydantic e suporta herança joined nativamente. |
| Escopo | **Backend e frontend completos**. | O vídeo da entrega demonstra as funcionalidades na interface. |
| Migrations | **Arquivos SQL numerados**, sem Alembic. | A disciplina é de banco de dados; SQL explícito é auditável pelo professor e o `docker-entrypoint-initdb.d` já carrega esses arquivos. |
| Granularidade das issues | **Uma issue por PR revisável**, com checklist interno. | Onze issues, todas com o número do requisito no título para casar com a rubrica. |

## Lacunas do modelo atual

O enunciado da Etapa 2 pressupõe estruturas que o schema da Etapa 1 não possui. Cada
lacuna abaixo é resolvida na issue de evolução do schema, que é pré-requisito de todas
as outras.

| Lacuna | Exigido por | Resolução |
| --- | --- | --- |
| Não existe conceito de internação | `vw_pacientes_internados` (`data_hora_saida IS NULL`) | Nova tabela `internacao` |
| `atendimento` não sabe em que unidade ocorreu | `sp_calcular_tempo_medio_espera`, `vw_estatisticas_atendimentos_mensal` | Nova coluna `atendimento.id_unidade` (FK obrigatória) |
| Não há horário de início de procedimento | `sp_calcular_tempo_medio_espera` | Nova coluna `procedimento_realizado.data_hora_inicio` |
| Não há onde gravar a média por procedimento | `trg_atualiza_media_procedimentos` | Nova coluna `procedimento.media_tempo_procedimento` |
| Não há tabela de auditoria | `trg_audita_atendimento` | Nova tabela `auditoria_atendimento` |
| `preceptor.titulacao` é texto livre | `vw_residentes_sem_supervisor` (precisa identificar doutores) | CHECK sobre conjunto fechado de valores |

## Arquitetura

### Camada de banco (`db/`)

Os arquivos são renumerados para respeitar a ordem de execução do
`docker-entrypoint-initdb.d`, que roda em ordem alfabética:

```
db/
├── 01_schema.sql       # DDL (evoluído)
├── 02_procedures.sql   # 3 stored procedures
├── 03_triggers.sql     # 3 triggers + suas funções
├── 04_views.sql        # 3 views
├── 05_seed.sql         # dados de exemplo (renomeado de 02_seed.sql)
└── consultas.sql       # consultas analíticas da Etapa 1 (referência)
```

O seed roda **por último**, depois das triggers. Isso é intencional: o banco sobe já com
`media_tempo_procedimento` calculada pela trigger e com linhas em
`auditoria_atendimento`, de modo que as views retornam dados no primeiro
`docker compose up`. O `docker-compose.yaml` precisa montar os cinco arquivos.

### Camada de aplicação (`backend/app/`)

```
backend/app/
├── main.py
├── config.py
├── db/
│   ├── base.py         # DeclarativeBase
│   └── session.py      # async engine, async_sessionmaker, dependency get_session
├── models/             # entidades mapeadas (substitui SQL cru)
├── schemas/            # Pydantic (mantido)
├── repositories/       # reescritos com a DSL do SQLAlchemy
├── api/                # routers (paths preservados)
└── scripts/
    └── demo_concorrencia.py
```

`app/core/database.py` (pool psycopg) é removido junto com os repositories em SQL cru.

## Requisito 1 — Stored procedures

**`sp_registrar_atendimento_completo(p_data_hora, p_duracao_minutos, p_id_paciente, p_id_residente, p_id_preceptor, p_id_unidade, p_procedimentos JSONB) RETURNS INTEGER`**

Insere o atendimento e itera sobre `jsonb_array_elements(p_procedimentos)` inserindo cada
`procedimento_realizado`. Retorna o `id_atendimento` criado. A atomicidade vem do bloco de
função do PostgreSQL: qualquer erro no meio do laço reverte também o INSERT do
atendimento. Um bloco `EXCEPTION` traduz violação de FK e de CHECK em mensagem legível
antes de relançar.

Formato esperado de `p_procedimentos`:

```json
[{"id_procedimento": 1, "quantidade": 2, "tempo_real_minutos": 30, "data_hora_inicio": "2026-06-01T08:15:00", "observacao": null}]
```

**`sp_calcular_tempo_medio_espera() RETURNS TABLE (id_unidade INT, nome_unidade VARCHAR, tempo_medio_espera_minutos NUMERIC)`**

Para cada unidade, média da diferença entre `atendimento.data_hora` (chegada) e
`MIN(procedimento_realizado.data_hora_inicio)` daquele atendimento. Atendimentos sem
procedimento registrado são excluídos do cálculo.

**`sp_reajustar_escala(p_id_residente INT, p_dia_origem VARCHAR, p_turno_origem VARCHAR, p_dia_destino VARCHAR, p_turno_destino VARCHAR)`**

Move todas as escalas do residente do dia/turno de origem para o de destino. Antes de
alterar, verifica se o destino já está ocupado pelo mesmo residente (em qualquer unidade)
e aborta com `RAISE EXCEPTION` sem alterar nada.

## Requisito 2 — Triggers

**`trg_check_sobreposicao_escala`** — BEFORE INSERT OR UPDATE em `escala`.

A constraint `uq_escala_unidade_dia_turno_residente` já impede duplicata do mesmo
residente na *mesma* unidade. A trigger cobre o caso que a constraint declarativa não
alcança: o mesmo residente escalado no mesmo dia e turno em **unidades diferentes**.
Essa divisão de responsabilidade entre constraint e trigger é o exemplo central do
relatório sobre quando usar cada mecanismo.

**`trg_audita_atendimento`** — AFTER INSERT OR UPDATE OR DELETE em `atendimento`.

Grava em `auditoria_atendimento` usando `to_jsonb(OLD)` e `to_jsonb(NEW)`, `current_user`
e `now()`. Em INSERT, `dados_antigos` é nulo; em DELETE, `dados_novos` é nulo.

**`trg_atualiza_media_procedimentos`** — AFTER INSERT em `procedimento_realizado`.

Recalcula `procedimento.media_tempo_procedimento` como a média de `tempo_real_minutos`
daquele procedimento em todos os atendimentos.

## Requisito 3 — Views

**`vw_pacientes_internados`** — `DISTINCT ON (id_paciente)` sobre `internacao` ordenado por
`data_hora_entrada DESC`, filtrando `data_hora_saida IS NULL` na linha mais recente.
Expõe paciente, unidade e tempo de internação.

**`vw_residentes_sem_supervisor`** — residentes com escala ativa cujo preceptor tem
`titulacao <> 'DOUTOR'` (e não `POS_DOUTOR`). Expõe residente, unidade, dia, turno e a
titulação do preceptor responsável.

**`vw_estatisticas_atendimentos_mensal`** — agregação por `date_trunc('month', data_hora)`
e unidade, com total de atendimentos, média de duração e os procedimentos mais
frequentes do período.

## Requisito 4 — ORM

Modelos em `app/models/`, um arquivo por agregado. A especialização do DER é mapeada com
**joined table inheritance**: `Pessoa` como base polimórfica, `Paciente` e `Profissional`
herdando dela, `Preceptor` e `Residente` herdando de `Profissional`. É o recurso que faz o
mapeamento objeto-relacional espelhar o modelo conceitual e é o principal argumento do
relatório sobre a escolha da ORM.

Demonstrações exigidas pelo enunciado e onde cada uma aparece:

- **Mapeamento objeto-relacional** — herança joined das cinco classes de pessoa.
- **Sessões e transações** — `async with session.begin()` nos endpoints de escrita.
- **DSL, sem SQL cru** — todos os repositories usam `select()`, `where()`, `join()`.
- **Lazy vs eager loading** — a listagem de atendimentos usa `selectinload` para os
  procedimentos; um endpoint mantém lazy de propósito para evidenciar o N+1 no log de SQL
  (`echo=True`), material direto para o vídeo.

Procedures são chamadas via `session.execute(text("SELECT sp_..."))`, que é a forma
idiomática de invocar rotinas do banco pela ORM. Views são mapeadas como modelos
read-only e consultadas pela DSL normal.

Os paths dos endpoints existentes são preservados para não quebrar o frontend.

## Requisito 5 — Consultas avançadas com ORM

1. Preceptores que supervisionaram residentes que atenderam pacientes com
   `is_flamengo = TRUE`.
2. Para cada paciente, seu último atendimento com data/hora, residente, preceptor e lista
   de procedimentos.
3. Percentual de procedimentos de alto risco realizados por cada residente.

Cada uma vira um endpoint em `app/api/analytics.py` e é escrita exclusivamente com a DSL.

## Requisito 6 — Concorrência

`backend/app/scripts/demo_concorrencia.py` abre duas sessões async que tentam escalar o
mesmo residente no mesmo dia, turno e unidade simultaneamente. A estratégia é **lock
pessimista**: a leitura de verificação usa `with_for_update()`, então a transação B fica
bloqueada até o commit de A, revalida a condição ao acordar e é rejeitada.

O script emite um log com carimbo de tempo mostrando a linha do tempo das duas
transações. A UNIQUE e a trigger permanecem como rede de segurança — o relatório explica
por que o lock sozinho não bastaria caso a verificação e a inserção não estivessem na
mesma transação.

Um teste em `backend/tests/` reproduz o cenário e afirma que exatamente uma das duas
transações teve sucesso.

## Frontend

Telas novas dentro do padrão de sidebar e tabela que a `page.tsx` já usa:

- Pacientes internados, residentes sem supervisor e estatísticas mensais (as três views).
- Formulário de atendimento completo, enviando vários procedimentos numa única chamada
  que aciona `sp_registrar_atendimento_completo`.
- Escalas, com ação de reajuste chamando `sp_reajustar_escala` e exibindo a mensagem de
  erro quando há conflito.
- Visualizador de `auditoria_atendimento`, mostrando o diff entre `dados_antigos` e
  `dados_novos`.

Como a `page.tsx` já passa de 950 linhas, as telas novas entram como componentes
separados em `frontend/components/`, e as views existentes são extraídas na mesma medida
em que forem tocadas.

## Testes

`backend/tests/` é estendido para cobrir cada procedure (caso feliz e rollback), cada
trigger (inclusive os INSERTs que devem ser rejeitados), cada view, os endpoints
migrados para a ORM, as três consultas avançadas e o cenário de concorrência.

## Entrega

- Tag `etapa-1` publicada antes da substituição dos repositories.
- `docs/modelagem.md` e o DER atualizados com `internacao`, `auditoria_atendimento` e as
  colunas novas.
- `docs/relatorio-etapa2.md`, de duas páginas, cobrindo triggers vs procedures e a
  escolha da ORM.
- README atualizado.
- Vídeo de até 8 minutos.

## Issues

Milestone `Etapa 2`. A #3 destrava #4, #5, #6 e #7; a #7 destrava #8 e #9, que destravam
a #10; a #11 depende da #7; a #12 depende do backend; a #13 fecha tudo.

| Issue | Título | Requisito | Pontos |
| --- | --- | --- | --- |
| #3 | Evolução do schema | pré-requisito | — |
| #4 | Stored procedures | 1 | 1,5 |
| #5 | Triggers | 2 | 1,5 |
| #6 | Views | 3 | 1,0 |
| #7 | SQLAlchemy: setup e mapeamento | 4 | 2,0 |
| #8 | Migrar CRUD para a ORM | 4 | (idem) |
| #9 | Migrar analíticos e expor procedures/views | 4 | (idem) |
| #10 | Consultas avançadas com ORM | 5 | 1,0 |
| #11 | Concorrência e transações | 6 | 1,0 |
| #12 | Telas do frontend | — | — |
| #13 | Documentação, relatório e vídeo | 7 | +1,0 |
