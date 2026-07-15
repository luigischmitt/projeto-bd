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
│   ├── 01_schema.sql      # CREATE TABLE e constraints
│   ├── 02_seed.sql        # dados de teste
│   └── consultas.sql      # 4 consultas analíticas (referência)
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   └── app/               # API FastAPI
├── frontend/              # UI Next.js
├── docs/
│   ├── modelagem.md       # DER, cardinalidades, 3FN, modelo relacional
│   └── diagrama-der.pdf
├── images/
│   └── print-der.png
└── docker-compose.yaml
```

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

No **primeiro** start (volume vazio), os scripts `db/01_schema.sql` e `db/02_seed.sql` são aplicados automaticamente.

Para reiniciar o banco do zero (reaplica schema e seed):

```bash
docker compose down -v
docker compose up -d
```

#### Opção B — PostgreSQL local

```bash
createdb -U postgres hospital_yuska
psql -U postgres -d hospital_yuska -f db/01_schema.sql
psql -U postgres -d hospital_yuska -f db/02_seed.sql
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
```

```powershell
# Windows
copy .env.example .env
```

```bash
# Linux / macOS
cp .env.example .env
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

```powershell
# Windows (PowerShell)
$env:NEXT_PUBLIC_API_URL="http://localhost:8000"
npm run dev
```

```bash
# Linux / macOS
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

## Scripts SQL

| Arquivo | Função |
|---------|--------|
| `db/01_schema.sql` | Cria as tabelas e constraints (PK, FK, CHECK, UNIQUE, NOT NULL) |
| `db/02_seed.sql` | Insere massa de dados de teste |
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
pip install pytest
pytest app/tests/test_api.py
```

Os testes de integração são ignorados se o PostgreSQL não estiver disponível.

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
| `GET` | `/atendimentos` | Lista atendimentos cadastrados |
| `POST` | `/atendimentos` | Cria atendimento |
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

- [docs/modelagem.md](docs/modelagem.md) — DER, cardinalidades, especialização, 3FN e modelo relacional  
- [docs/diagrama-der.pdf](docs/diagrama-der.pdf) — diagrama entidade-relacionamento  
- [images/print-der.png](images/print-der.png) — visão rápida do DER  

## Licença

MIT — ver [LICENSE](LICENSE).
