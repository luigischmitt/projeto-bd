# Sistema de Gestão Hospitalar Dra. Yuska

Projeto acadêmico de Banco de Dados. Etapa 1: modelagem relacional, schema PostgreSQL com SQL puro, API FastAPI e interface Next.js para CRUD e relatórios analíticos. Etapa 2: stored procedures, triggers, views, migração completa da API para SQLAlchemy 2.0 async (DSL, sem SQL cru), consultas analíticas avançadas e uma demonstração de controle de concorrência com lock pessimista.

## Índice

- [Integrantes](#integrantes)
- [Stack](#stack)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Pré-requisitos](#pré-requisitos)
- [Instalação e execução](#instalação-e-execução)
- [Scripts SQL](#scripts-sql)
- [Scripts do frontend](#scripts-do-frontend)
- [Testes da API](#testes-da-api)
- [Demo de concorrência (lock pessimista)](#demo-de-concorrência-lock-pessimista)
- [Endpoints principais](#endpoints-principais)
- [Documentação da modelagem, relatório e vídeo](#documentação-da-modelagem-relatório-e-vídeo)
- [Licença](#licença)

## Integrantes

| Nome |
|------|
| LUIGI EMANUEL MARTINS SCHMITT |
| MIGUEL DE QUEIROZ FERNANDES SOARES |
| RAFAEL TORRES NOBREGA GOMES |

## Stack

| Camada | Tecnologia |
|--------|------------|
| Banco de dados | PostgreSQL 16 (stored procedures, triggers e views em PL/pgSQL) |
| Backend | FastAPI + Uvicorn + SQLAlchemy 2.0 (async, DSL) sobre o driver psycopg 3 |
| Frontend | Next.js 16 + React 19 + TypeScript + Tailwind CSS 4 |
| Infra local | Docker Compose (apenas o PostgreSQL) |

A partir da Etapa 2 a API é **100% SQLAlchemy**: não há mais SQL cru nos repositories (`text()` só é usado para chamar as stored procedures, que são objetos de banco). O driver `psycopg` continua presente apenas como driver da engine assíncrona (`postgresql+psycopg://`).

## Estrutura do repositório

```
projeto-bd/
├── db/
│   ├── 01_schema.sql       # CREATE TABLE e constraints
│   ├── 02_procedures.sql   # stored procedures (Etapa 2)
│   ├── 03_triggers.sql     # triggers (Etapa 2)
│   ├── 04_views.sql        # views (Etapa 2)
│   ├── 05_seed.sql         # dados de teste (roda por último, com triggers já ativas)
│   └── consultas.sql       # 4 consultas analíticas da Etapa 1 (referência)
├── backend/
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── pytest.ini
│   ├── .env.example
│   ├── app/
│   │   ├── main.py         # app FastAPI, CORS, registro de rotas
│   │   ├── config.py       # variáveis de ambiente (DATABASE_URL, SQLALCHEMY_ECHO)
│   │   ├── api/            # camada HTTP (routers por domínio)
│   │   ├── db/              # DeclarativeBase, engine assíncrona, get_session
│   │   ├── models/           # mapeamento ORM (SQLAlchemy 2.0), um arquivo por agregado
│   │   ├── schemas/        # modelos Pydantic (request/response)
│   │   ├── repositories/   # acesso a dados via DSL do SQLAlchemy — sem SQL cru
│   │   └── scripts/          # demo_concorrencia.py (Req 6)
│   └── tests/              # testes de integração da API e do banco (79 testes)
├── frontend/               # UI Next.js
├── docs/
│   ├── modelagem.md            # DER, cardinalidades, 3FN, modelo relacional (Etapa 1 e 2)
│   ├── relatorio-etapa2.md     # discussões triggers/procedures e escolha da ORM
│   ├── roteiro-video.md        # roteiro do vídeo de demonstração
│   ├── diagrama-der.pdf        # diagrama entidade-relacionamento (recorte da Etapa 1)
│   └── print-der.png           # visão rápida do DER (idem)
└── docker-compose.yaml
```

### Backend — organização em camadas

| Pasta | Responsabilidade |
|-------|------------------|
| `app/api/` | Rotas HTTP: validação de entrada, status codes, chamada aos repositories |
| `app/schemas/` | Contratos da API (Pydantic): create, update, list, response |
| `app/models/` | Mapeamento ORM (SQLAlchemy 2.0): `Pessoa`/`Paciente`/`Profissional`/`Preceptor`/`Residente` (herança joined), `Unidade`, `Procedimento`, `Atendimento`, `ProcedimentoRealizado`, `Escala`, `Internacao`, `AuditoriaAtendimento`, e as views read-only em `models/views.py` |
| `app/repositories/` | Consultas com a DSL do SQLAlchemy (`select()`/`join()`/`func`) e transações (`session.begin()`) — sem lógica HTTP |
| `app/db/` | `DeclarativeBase`, engine assíncrona (`postgresql+psycopg://`) e a dependency `get_session` |
| `app/scripts/` | `demo_concorrencia.py` — demonstração de lock pessimista (Req 6) |
| `app/config.py` | Settings via pydantic-settings |

Routers em `app/api/`:

| Arquivo | Prefixo | Domínio |
|---------|---------|---------|
| `pacientes.py` | `/pacientes` | CRUD de pacientes + atendimentos do paciente |
| `residentes.py` | `/residentes` | CRUD de residentes + tempo médio |
| `preceptores.py` | `/preceptores` | CRUD de preceptores |
| `unidades.py` | `/unidades` | Listagem de unidades hospitalares |
| `atendimentos.py` | `/atendimentos` | CRUD de atendimentos + procedimentos + atendimento completo (procedure) |
| `escalas.py` | `/escalas` | Listagem da grade semanal + reajuste (procedure) |
| `views.py` | `/views` | Leitura das três views da Etapa 2 |
| `auditoria.py` | `/auditoria` | Histórico de auditoria de `atendimento` |
| `analytics.py` | `/analytics` | Relatórios analíticos da Etapa 1 e da Etapa 2 |

## Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) e Docker Compose **ou** PostgreSQL 16 instalado localmente
- Python 3.11+ (recomendado)
- Node.js 20+ e npm

## Instalação e execução

Ordem sugerida: **banco → backend → frontend**.

### 1. Banco de dados

#### Opção A — Docker (recomendado)

Na raiz do repositório:

```bash
docker compose up -d
```

Isso sobe o PostgreSQL na porta `5432` com:

| Variável | Valor |
|----------|-------|
| Usuário | `postgres` |
| Senha | `postgres` |
| Database | `hospital_yuska` |

No **primeiro** start (volume vazio), os scripts de `db/` são aplicados automaticamente em ordem alfabética: schema, procedures, triggers, views e, por último, o seed.

Para reiniciar o banco do zero (reaplica schema e seed):

```bash
docker compose down -v
docker compose up -d
```

A ordem de carga é sempre **schema → procedures → triggers → views → seed**: o seed roda por último de propósito, para que as triggers já estejam ativas quando os dados de teste entrarem (por isso o banco já sobe com `procedimento.media_tempo_procedimento` calculada e linhas em `auditoria_atendimento`).

#### Opção B — PostgreSQL local

```bash
createdb -U postgres hospital_yuska
psql -U postgres -d hospital_yuska -f db/01_schema.sql
psql -U postgres -d hospital_yuska -f db/02_procedures.sql
psql -U postgres -d hospital_yuska -f db/03_triggers.sql
psql -U postgres -d hospital_yuska -f db/04_views.sql
psql -U postgres -d hospital_yuska -f db/05_seed.sql
```

#### Opção C — container Docker isolado (útil para testar sem afetar o `docker compose` local)

```bash
docker run --rm -d --name pg-hospital -e POSTGRES_PASSWORD=postgres -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=hospital_yuska -p 55462:5432 postgres:16

cd db
for f in 01_schema.sql 02_procedures.sql 03_triggers.sql 04_views.sql 05_seed.sql; do
  docker exec -i pg-hospital psql -U postgres -d hospital_yuska -v ON_ERROR_STOP=1 < "$f"
done
```

`DATABASE_URL` correspondente: `postgresql://postgres:postgres@localhost:55462/hospital_yuska`.

### 2. Backend (API)

```bash
cd backend
python -m venv venv
```

Ative o ambiente virtual:

```powershell
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1
```

```bash
# Linux / macOS
source venv/bin/activate
```

Instale as dependências e configure o `.env`:

```bash
pip install -r requirements.txt
cp .env.example .env   # Linux / macOS
# copy .env.example .env   # Windows
```

Conteúdo esperado do `.env`:

```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/hospital_yuska
```

Opcionalmente, para ver o SQL gerado pela ORM no console (útil para observar as estratégias de eager/lazy loading e o N+1 intencional de `GET /pacientes/{id}/atendimentos`, ver seção do vídeo em [`docs/roteiro-video.md`](docs/roteiro-video.md)):

```
SQLALCHEMY_ECHO=1
```

Suba a API:

```bash
uvicorn app.main:app --reload
```

| Recurso | URL |
|---------|-----|
| API | http://localhost:8000 |
| Documentação Swagger | http://localhost:8000/docs |

### 3. Frontend

Em outro terminal:

```bash
cd frontend
npm install
npm run dev
```

A interface fica em http://localhost:3000.

Por padrão a UI chama a API em `http://localhost:8000`. Para apontar para outro host:

```bash
# Linux / macOS
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

```powershell
# Windows (PowerShell)
$env:NEXT_PUBLIC_API_URL="http://localhost:8000"
npm run dev
```

## Scripts SQL

| Arquivo | Função |
|---------|--------|
| `db/01_schema.sql` | Cria as tabelas e constraints (PK, FK, CHECK, UNIQUE, NOT NULL), incluindo `internacao`, `auditoria_atendimento` e as colunas novas da Etapa 2 |
| `db/02_procedures.sql` | `sp_registrar_atendimento_completo`, `sp_calcular_tempo_medio_espera`, `sp_reajustar_escala` |
| `db/03_triggers.sql` | `trg_check_sobreposicao_escala`, `trg_audita_atendimento`, `trg_atualiza_media_procedimentos` |
| `db/04_views.sql` | `vw_pacientes_internados`, `vw_residentes_sem_supervisor`, `vw_estatisticas_atendimentos_mensal` |
| `db/05_seed.sql` | Insere massa de dados de teste (roda por último, já com as triggers ativas) |
| `db/consultas.sql` | Quatro consultas analíticas da Etapa 1 (para demonstração no `psql`) |

Executar as consultas analíticas no banco já populado:

```bash
psql -U postgres -d hospital_yuska -f db/consultas.sql
```

As mesmas consultas também estão expostas na API em `/analytics/*` e no painel do frontend.

### Consultas em `consultas.sql`

1. Ranking de residentes por número de atendimentos
2. Preceptores com mais de 5 supervisões em um mês (exemplo: junho/2026)
3. Quantidade de plantões por unidade e residente
4. Pacientes que nunca realizaram procedimento de risco `ALTO`

## Scripts do frontend

| Comando | Função |
|---------|--------|
| `npm run dev` | Servidor de desenvolvimento (porta 3000) |
| `npm run build` | Build de produção |
| `npm run start` | Serve o build de produção |
| `npm run lint` | ESLint |

## Testes da API

Com o banco acessível (schema, procedures, triggers, views e seed já carregados) e o venv do backend ativo:

```bash
cd backend
pip install -r requirements-dev.txt
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/hospital_yuska pytest
```

A suíte tem **79 testes** (integração da API, procedures, triggers, views, modelos ORM,
consultas analíticas avançadas, escalas e a demo de concorrência) e são ignorados
automaticamente se o PostgreSQL não estiver disponível no `DATABASE_URL`. Rodar um arquivo
específico: `pytest tests/test_triggers.py -v`.

## Demo de concorrência (lock pessimista)

Implementa o Req 6: duas transações async concorrentes disputam a mesma vaga de escala
(mesma unidade, dia, turno e residente) usando lock pessimista (`SELECT ... FOR UPDATE` na
linha do residente) para garantir que exatamente uma vença. Ver a justificativa completa
no docstring de `backend/app/scripts/demo_concorrencia.py`.

```bash
cd backend
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/hospital_yuska python -m app.scripts.demo_concorrencia
```

O script imprime a linha do tempo com carimbo relativo (`t=+SSS.mmm`), mostrando a
Transação B bloqueada até a A liberar o lock, e remove a escala de demonstração ao final
(reexecutável sem deixar resíduo). Parâmetros opcionais: `--id-unidade`, `--dia-semana`,
`--turno`, `--id-residente`, `--id-preceptor`, `--manter-escala` (não limpa ao final).

## Endpoints principais

Documentação interativa: http://localhost:8000/docs

### CRUD

| Método | Path | Descrição |
|--------|------|-----------|
| `GET` | `/pacientes` | Lista pacientes cadastrados |
| `POST` | `/pacientes` | Cadastra paciente |
| `PUT` | `/pacientes/{id}` | Atualiza paciente |
| `GET` | `/residentes` | Lista residentes cadastrados |
| `POST` | `/residentes` | Cadastra residente |
| `PUT` | `/residentes/{id}` | Atualiza residente |
| `GET` | `/preceptores` | Lista preceptores cadastrados |
| `POST` | `/preceptores` | Cadastra preceptor |
| `PUT` | `/preceptores/{id}` | Atualiza preceptor |
| `GET` | `/unidades` | Lista unidades hospitalares |
| `GET` | `/atendimentos` | Lista atendimentos cadastrados |
| `POST` | `/atendimentos` | Cria atendimento (exige `id_unidade`) |
| `GET` | `/pacientes/{id}/atendimentos` | Atendimentos do paciente |
| `GET` | `/atendimentos/{id}/procedimentos` | Procedimentos do atendimento |
| `DELETE` | `/atendimentos/{id}/procedimentos/{cod}` | Remove procedimento se não faturado |
| `GET` | `/residentes/tempo-medio` | Tempo médio de duração por residente |
| `POST` | `/atendimentos/completo` | Registra atendimento + procedimentos em uma transação (`sp_registrar_atendimento_completo`); FK/CHECK inválidos voltam **400** sem estado parcial |
| `GET` | `/escalas` | Grade semanal completa de escalas |
| `POST` | `/escalas/reajustar` | Move a escala de um residente para outro dia/turno (`sp_reajustar_escala`); destino ocupado vira **409** |

### Views (Etapa 2)

| Método | Path | Descrição |
|--------|------|-----------|
| `GET` | `/views/pacientes-internados` | `vw_pacientes_internados` |
| `GET` | `/views/residentes-sem-supervisor` | `vw_residentes_sem_supervisor` |
| `GET` | `/views/estatisticas-mensais` | `vw_estatisticas_atendimentos_mensal` |

### Auditoria (Etapa 2)

| Método | Path | Descrição |
|--------|------|-----------|
| `GET` | `/auditoria/atendimentos` | Histórico de INSERT/UPDATE/DELETE gravado por `trg_audita_atendimento` (aceita `?id_atendimento=`) |

### Analytics

| Método | Path | Descrição |
|--------|------|-----------|
| `GET` | `/analytics/ranking-residentes` | Ranking por nº de atendimentos |
| `GET` | `/analytics/preceptores-supervisao?mes=YYYY-MM` | Preceptores com >5 supervisões no mês |
| `GET` | `/analytics/plantoes-por-unidade` | Plantões por unidade/residente |
| `GET` | `/analytics/pacientes-sem-risco-alto` | Pacientes sem procedimento de risco alto |
| `GET` | `/analytics/tempo-medio-espera` | Tempo médio de espera por unidade (`sp_calcular_tempo_medio_espera`) |
| `GET` | `/analytics/preceptores-flamenguistas` | Preceptores que supervisionaram residentes que atenderam pacientes flamenguistas |
| `GET` | `/analytics/ultimo-atendimento-por-paciente` | Atendimento mais recente de cada paciente, com residente/preceptor/procedimentos |
| `GET` | `/analytics/percentual-alto-risco` | Percentual de procedimentos de risco ALTO por residente |

## Documentação da modelagem, relatório e vídeo

Tudo em [`docs/`](docs/):

| Arquivo | Conteúdo |
|---------|----------|
| [modelagem.md](docs/modelagem.md) | DER, cardinalidades, especialização, 3FN, modelo relacional e a evolução do modelo na Etapa 2 |
| [relatorio-etapa2.md](docs/relatorio-etapa2.md) | Triggers vs. procedures e a escolha do SQLAlchemy 2.0 async |
| [roteiro-video.md](docs/roteiro-video.md) | Roteiro cronometrado do vídeo de demonstração da Etapa 2 |
| [diagrama-der.pdf](docs/diagrama-der.pdf) | Diagrama entidade-relacionamento (PDF, recorte da Etapa 1 — o diagrama relacional vigente, com as entidades da Etapa 2, está em `modelagem.md`) |
| [print-der.png](docs/print-der.png) | Visão rápida do DER (PNG, idem) |

## Licença

MIT — ver [LICENSE](LICENSE).
