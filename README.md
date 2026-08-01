# Sistema de Gestão Hospitalar Dra. Yuska

Projeto acadêmico de Banco de Dados (Etapa 1): modelagem relacional, schema PostgreSQL com SQL puro, API FastAPI (sem ORM) e interface Next.js para CRUD e relatórios analíticos.

## Índice

- [Integrantes](#integrantes)
- [Stack](#stack)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Pré-requisitos](#pré-requisitos)
- [Instalação e execução](#instalação-e-execução)
- [Scripts SQL](#scripts-sql)
- [Scripts do frontend](#scripts-do-frontend)
- [Testes da API (opcional)](#testes-da-api-opcional)
- [Endpoints principais](#endpoints-principais)
- [Documentação da modelagem](#documentação-da-modelagem)
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
| Banco de dados | PostgreSQL 16 |
| Backend | FastAPI + Uvicorn + psycopg 3 (SQL puro) |
| Frontend | Next.js 16 + React 19 + TypeScript + Tailwind CSS 4 |
| Infra local | Docker Compose (apenas o PostgreSQL) |

## Estrutura do repositório

```
projeto-bd/
├── db/
│   ├── 01_schema.sql       # CREATE TABLE e constraints
│   ├── 02_procedures.sql   # stored procedures (Etapa 2)
│   ├── 03_triggers.sql     # triggers (Etapa 2)
│   ├── 04_views.sql        # views (Etapa 2)
│   ├── 05_seed.sql         # dados de teste
│   └── consultas.sql       # 4 consultas analíticas (referência)
├── backend/
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── pytest.ini
│   ├── .env.example
│   ├── app/
│   │   ├── main.py         # app FastAPI, CORS, registro de rotas
│   │   ├── config.py       # variáveis de ambiente (DATABASE_URL)
│   │   ├── api/            # camada HTTP (routers por domínio)
│   │   ├── core/           # infraestrutura (pool de conexões)
│   │   ├── schemas/        # modelos Pydantic (request/response)
│   │   └── repositories/   # acesso a dados (SQL puro)
│   └── tests/              # testes de integração da API
├── frontend/               # UI Next.js
├── docs/
│   ├── modelagem.md        # DER, cardinalidades, 3FN, modelo relacional
│   ├── diagrama-der.pdf    # diagrama entidade-relacionamento
│   └── print-der.png       # visão rápida do DER
└── docker-compose.yaml
```

### Backend — organização em camadas

| Pasta | Responsabilidade |
|-------|------------------|
| `app/api/` | Rotas HTTP: validação de entrada, status codes, chamada aos repositories |
| `app/schemas/` | Contratos da API (Pydantic): create, update, list, response |
| `app/repositories/` | Queries SQL com psycopg — sem lógica HTTP |
| `app/core/` | Pool assíncrono PostgreSQL e dependency `get_db` |
| `app/config.py` | Settings via pydantic-settings |

Routers em `app/api/`:

| Arquivo | Prefixo | Domínio |
|---------|---------|---------|
| `pacientes.py` | `/pacientes` | CRUD de pacientes + atendimentos do paciente |
| `residentes.py` | `/residentes` | CRUD de residentes + tempo médio |
| `preceptores.py` | `/preceptores` | CRUD de preceptores |
| `unidades.py` | `/unidades` | Listagem de unidades hospitalares |
| `atendimentos.py` | `/atendimentos` | CRUD de atendimentos + procedimentos |
| `analytics.py` | `/analytics` | Relatórios analíticos |

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

#### Opção B — PostgreSQL local

```bash
createdb -U postgres hospital_yuska
psql -U postgres -d hospital_yuska -f db/01_schema.sql
psql -U postgres -d hospital_yuska -f db/02_procedures.sql
psql -U postgres -d hospital_yuska -f db/03_triggers.sql
psql -U postgres -d hospital_yuska -f db/04_views.sql
psql -U postgres -d hospital_yuska -f db/05_seed.sql
```

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
| `db/01_schema.sql` | Cria as tabelas e constraints (PK, FK, CHECK, UNIQUE, NOT NULL) |
| `db/02_procedures.sql` | Stored procedures da Etapa 2 |
| `db/03_triggers.sql` | Triggers da Etapa 2 |
| `db/04_views.sql` | Views da Etapa 2 |
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

## Testes da API (opcional)

Com o banco acessível e o venv do backend ativo:

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

Os testes de integração em `backend/tests/` são ignorados automaticamente se o PostgreSQL não estiver disponível no `DATABASE_URL`.

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

### Analytics

| Método | Path | Descrição |
|--------|------|-----------|
| `GET` | `/analytics/ranking-residentes` | Ranking por nº de atendimentos |
| `GET` | `/analytics/preceptores-supervisao?mes=YYYY-MM` | Preceptores com >5 supervisões no mês |
| `GET` | `/analytics/plantoes-por-unidade` | Plantões por unidade/residente |
| `GET` | `/analytics/pacientes-sem-risco-alto` | Pacientes sem procedimento de risco alto |

## Documentação da modelagem

Tudo em [`docs/`](docs/):

| Arquivo | Conteúdo |
|---------|----------|
| [modelagem.md](docs/modelagem.md) | DER, cardinalidades, especialização, 3FN e modelo relacional |
| [diagrama-der.pdf](docs/diagrama-der.pdf) | Diagrama entidade-relacionamento (PDF) |
| [print-der.png](docs/print-der.png) | Visão rápida do DER (PNG) |

## Licença

MIT — ver [LICENSE](LICENSE).
