# Roteiro do vídeo — Etapa 2

Duração-alvo: **8 minutos**. Blocos com tempo alocado por peso de nota (Etapa 2 pesa mais
em triggers e na migração para ORM, que somam três issues cada). Cada bloco diz o que
abrir, o que clicar/digitar e o que apontar na tela.

## Roteiro alternativo — 100% pela UI

Use este roteiro se quiser demonstrar **tudo pelo frontend** (`http://localhost:3000`), sem
`psql` na gravação.

| Requisito | Onde na UI | O que fazer |
|-----------|------------|-------------|
| `sp_registrar_atendimento_completo` | Atendimentos → Atendimento completo | Cadastrar com procedimento inválido (409/400), depois com IDs válidos |
| `sp_reajustar_escala` | Escalas | Reajustar para dia/turno ocupado (409), depois destino livre |
| `trg_check_sobreposicao_escala` | Escalas → bloco "Demonstrar trg_check_sobreposicao_escala" | Residente 11, unidade 2, SEG/MANHA → botão "Tentar cadastrar escala" (409) |
| `trg_audita_atendimento` | Atendimentos → Novo atendimento, depois Auditoria | Cadastrar atendimento; abrir Auditoria e apontar nova linha |
| `trg_atualiza_media_procedimentos` | Atendimento completo, depois Análises avançadas → Média por procedimento | Registrar procedimentos; "Atualizar catálogo" e apontar coluna média observada |
| `sp_calcular_tempo_medio_espera` | Análises avançadas → Tempo médio de espera | Tabela carrega ao abrir a tela |
| 3 views SQL | Visões (3 telas) | Pacientes internados, Residentes sem supervisor, Estatísticas mensais |
| Consultas ORM avançadas | Análises avançadas → Consultas avançadas | Três cards carregam ao abrir |
| Relatórios Etapa 1 | Relatórios → Painel analítico | Botões de ranking, plantões, etc. |
| ORM / N+1 (opcional) | Terminal com `SQLALCHEMY_ECHO=1` + Consultas → Ver atendimentos | Só se quiser mostrar log de SQL no bloco ORM |

**Ordem sugerida (≈6 min só na UI):** Atendimento completo → Escalas (reajuste + trigger) →
Novo atendimento + Auditoria → Análises avançadas (média, tempo, consultas) →
Visões (3) → Painel analítico.

## Preparação (antes de gravar, fora do tempo do vídeo)

1. Subir o Postgres com os cinco scripts na ordem (ex.: `docker compose up -d`, ou o
   container isolado da seção "Instalação e execução" do `README.md`).
2. Backend: `cd backend && DATABASE_URL=... SQLALCHEMY_ECHO=1 uvicorn app.main:app --reload`
   — o `SQLALCHEMY_ECHO=1` é essencial para o bloco 4 (log de SQL).
3. Frontend: `cd frontend && npm run dev`, aberto em `http://localhost:3000`.
4. Um segundo terminal, grande o suficiente para ler os logs do backend (bloco 2 e 4) e
   outro para o script de concorrência (bloco 5).
5. Deixar `db/05_seed.sql` recarregado (banco limpo) para os números citados abaixo
   corresponderem ao que aparece na tela.

## Bloco 1 — Abertura e procedures (0:00 – 1:40, ~1min40)

**0:00–0:20 — Abertura.** Tela: slide ou README no editor. Falar: nome do projeto,
integrantes, e que o vídeo cobre a Etapa 2 (procedures, triggers, views, ORM e
concorrência) sobre o schema herdado da Etapa 1.

**0:20–1:00 — `sp_registrar_atendimento_completo`.** Tela: frontend, aba **Atendimentos →
Atendimento completo**. Preencher o formulário e adicionar 1 procedimento com
`id_procedimento` inexistente (ex. `9999`). Clicar em salvar. Apontar o erro **400** na
tela, com a mensagem de FK inválida. Dizer: "nada foi criado — a procedure desfez o
`INSERT` do atendimento inteiro, não só o do procedimento, via savepoint implícito do
bloco PL/pgSQL". Corrigir o `id_procedimento` para um válido (1 a 5) e reenviar; apontar o
**201** e o atendimento novo na listagem.

**1:00–1:40 — `sp_reajustar_escala`.** Tela: frontend, aba **Escalas**. Clicar
"Reajustar" numa linha e escolher um dia/turno onde o mesmo residente já está escalado
(ver a própria grade na tela para escolher um destino ocupado). Apontar o **409** com a
mensagem de conflito. Repetir escolhendo um destino livre; apontar a linha atualizando
com o novo dia/turno.

## Bloco 2 — Triggers disparando em tempo real (1:40 – 3:40, ~2min)

Este é o bloco mais forte da entrega — mostrar a trigger de auditoria populando **sozinha**
depois de uma alteração feita fora da API.

**1:40–2:20 — `trg_check_sobreposicao_escala`: UNIQUE vs. trigger.** Tela: terminal com
`psql` conectado ao banco. Rodar um `INSERT` em `escala` duplicando um residente na
**mesma unidade**, mesmo dia/turno — apontar o erro `duplicate key value violates unique
constraint "uq_escala_unidade_dia_turno_residente"`. Rodar um segundo `INSERT`, agora numa
**unidade diferente**, mesmo dia/turno, mesmo residente — apontar o erro distinto,
`ERROR: Residente ... já está escalado no dia ... turno ... em outra unidade`, levantado
pela trigger. Falar a diferença: a UNIQUE resolve dentro da mesma unidade; a trigger cobre
o buraco entre unidades diferentes, que a UNIQUE não alcança.

**2:20–3:40 — `trg_audita_atendimento` e `trg_atualiza_media_procedimentos`.** Tela:
dividir entre `psql` e o frontend (aba **Auditoria**), ou dois terminais lado a lado.
Rodar `SELECT count(*) FROM auditoria_atendimento;` no `psql` para anotar o número atual.
Rodar um `UPDATE atendimento SET duracao_minutos = duracao_minutos + 5 WHERE
id_atendimento = 1;` diretamente no banco (sem passar pela API, para provar que a trigger
é automática e inescapável). Atualizar a aba **Auditoria** no frontend (ou rodar o
`SELECT count(*)` de novo) e apontar a nova linha aparecendo **sozinha**, com o diff campo
a campo entre `dados_antigos`/`dados_novos`. Em seguida, rodar um `INSERT` em
`procedimento_realizado` para um procedimento existente e mostrar
`procedimento.media_tempo_procedimento` recalculada com um `SELECT` simples — sem nenhum
código de aplicação envolvido nos dois casos.

## Bloco 3 — Views (3:40 – 4:40, ~1min)

Tela: frontend, grupo **Visões**. Abrir as três telas em sequência, uma frase por tela:

- **Pacientes internados** (`vw_pacientes_internados`): apontar que só aparece a
  internação **mais recente** de cada paciente, e só se ainda estiver em curso.
- **Residentes sem supervisor** (`vw_residentes_sem_supervisor`): apontar que só lista
  escalas cujo preceptor não é `DOUTOR`/`POS_DOUTOR`.
- **Estatísticas mensais** (`vw_estatisticas_atendimentos_mensal`): apontar o total de
  atendimentos, duração média e o array dos procedimentos mais frequentes por
  unidade/mês.

## Bloco 4 — ORM: herança joined e o log de SQL evidenciando N+1 (4:40 – 6:40, ~2min)

**4:40–5:20 — Herança joined no código.** Tela: editor, `backend/app/models/pessoa.py`.
Apontar a expressão `CASE`/`EXISTS` do `polymorphic_on` e explicar em uma frase: o schema
não tem coluna discriminadora, então o SQLAlchemy resolve o tipo concreto (`Paciente`,
`Preceptor`, `Residente`) por uma expressão SQL computada, não por uma coluna física.

**5:20–6:00 — N+1 no log de SQL.** Tela: terminal com o log do `uvicorn` (com
`SQLALCHEMY_ECHO=1` já ligado). No frontend, abrir **Pacientes → ver atendimentos de um
paciente** (endpoint `GET /pacientes/{id}/atendimentos`). Voltar ao terminal e apontar no
log **múltiplos `SELECT` isolados**, um por atendimento, para `residente`/`preceptor`/
`unidade` — o N+1 clássico. Explicar: é intencional (`lazyload()` desliga o eager padrão
só nesse endpoint), para servir de material didático.

**6:00–6:40 — Contraste com eager loading.** Tela: mesmo terminal. Recarregar a listagem
geral de **Atendimentos** (`GET /atendimentos`) e apontar no log um único `SELECT` com
`JOIN` trazendo paciente e unidade juntos (`joinedload()` explícito) — o oposto do bloco
anterior. Uma frase de fechamento: a estratégia de loading é escolhida por consulta, não
imposta globalmente pelo ORM.

## Bloco 5 — Demo de concorrência (6:40 – 7:50, ~1min10)

Tela: terminal. Rodar:

```bash
cd backend
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/hospital_yuska python -m app.scripts.demo_concorrencia
```

Enquanto a saída aparece (leva ~2s por causa do `atraso_com_lock` proposital), apontar em
tempo real: a Transação B solicitando o lock e ficando bloqueada (`t=+0.3s` até `t=+2.0s`
aproximadamente) enquanto a Transação A ainda o detém; o momento em que A libera e B
imediatamente revalida e rejeita; e a linha final "**Total de transações bem-sucedidas: 1
(esperado: 1)**". Uma frase explicando a estratégia: lock pessimista na linha do
residente (`SELECT ... FOR UPDATE`), porque a vaga em disputa ainda não existe para travar
diretamente.

## Bloco 6 — Encerramento (7:50 – 8:00)

Tela: README ou slide final. Mencionar rapidamente que a suíte de testes automatizados
(79 testes) cobre tudo o que foi demonstrado, e que as consultas analíticas avançadas
(Req 5) e o relatório completo estão documentados em `docs/relatorio-etapa2.md`.
