# Relatório — Etapa 2

Sistema de Gestão Hospitalar Dra. Yuska. Este relatório cobre as duas discussões exigidas
pelo enunciado: a divisão de responsabilidade entre triggers e procedures, e a escolha do
SQLAlchemy 2.0 async como ORM. As demais entregas (procedures, triggers, views, migração
para ORM, consultas avançadas, concorrência e telas) estão descritas nos PRs [#15](https://github.com/luigischmitt/projeto-bd/pull/15)–[#25](https://github.com/luigischmitt/projeto-bd/pull/25) e no código.

## 1. Triggers versus procedures

Regra adotada: **trigger** quando a regra pertence ao banco e precisa disparar sozinha,
automática e inescapável, independente de qual cliente manipula os dados; **procedure**
quando a regra é uma operação de negócio que a aplicação invoca deliberadamente, com
parâmetros e um resultado a devolver.

**O exemplo central.** `escala` tem a constraint `UNIQUE (id_unidade, dia_semana, turno,
id_residente)`. Ela impede o mesmo residente duas vezes no mesmo dia/turno **dentro da
mesma unidade** — igualdade de tupla, o que uma `UNIQUE` composta resolve. O que ela
**não alcança** é o residente escalado no mesmo dia/turno em **unidades diferentes**:
linhas com `id_unidade` distinto não colidem na `UNIQUE`, porque a própria coluna que
diferencia integra a chave. Fechar esse buraco exige uma regra que enxergue outras linhas
ignorando uma das colunas da unicidade — o que uma constraint declarativa não expressa por
definição (`CHECK` só vê a própria linha; `UNIQUE` só vê igualdade de tupla completa). É
esse gap semântico, não preferência estilística, que justifica `trg_check_sobreposicao_escala`
(`BEFORE INSERT OR UPDATE`): um `SELECT` correlacionado busca outra linha do mesmo
residente, mesmo dia/turno, unidade diferente, e dispara `RAISE EXCEPTION` se encontrar. A
trigger não reimplementa o que a `UNIQUE` já cobre — a exclusão `id_unidade <>
NEW.id_unidade` no seu `WHERE` é o limite exato onde uma termina e a outra assume.

A divisão é auditável, não só documentada: `test_escala_mesma_unidade_e_bloqueada_pela_unique_nao_pela_trigger`
(`backend/tests/test_triggers.py`) provoca a duplicata na mesma unidade e afirma
`psycopg.errors.UniqueViolation`; um teste gêmeo provoca o conflito entre unidades e afirma
`RaiseException`. Se a trigger fosse removida, o primeiro teste continuaria passando; se a
`UNIQUE` fosse removida, o segundo continuaria — prova de que a responsabilidade não se
sobrepõe.

**As outras duas triggers.** `trg_audita_atendimento` (`AFTER INSERT/UPDATE/DELETE`) grava
`to_jsonb(OLD)`/`to_jsonb(NEW)` e `current_user`. Auditoria só cumpre sua função se for
impossível de burlar: se dependesse de a aplicação lembrar de chamar algo, um `UPDATE`
direto via `psql` ou um script de manutenção deixaria buracos no histórico — a trigger
garante que toda mutação em `atendimento`, por qualquer via, gera registro.
`trg_atualiza_media_procedimentos` (`AFTER INSERT` em `procedimento_realizado`) recalcula
`procedimento.media_tempo_procedimento`: é uma invariante de dado que precisa se manter
consistente com sua origem em toda inserção, não uma ação que um fluxo de negócio decide
executar.

**Por que registrar atendimento é procedure.** `sp_registrar_atendimento_completo` é uma
operação explicitamente invocada pela aplicação (`POST /atendimentos/completo`), com
parâmetros de entrada e retorno (`id_atendimento`). Não há evento de banco que dispare
"registrar um atendimento completo" sozinho — é sempre uma decisão de negócio de um
cliente da API. Mesmo raciocínio para `sp_reajustar_escala`: mover a escala de um
residente é uma ação deliberada via `CALL`, não reação a um evento. A atomicidade não usa
`SAVEPOINT` manual: um bloco PL/pgSQL com `EXCEPTION` cria um savepoint implícito no início
— se um `INSERT` do laço de procedimentos falhar (FK/`CHECK`), o runtime desfaz tudo desde
esse savepoint, inclusive o `INSERT` do atendimento já feito no mesmo bloco, antes do
handler traduzir a mensagem. A API traduz esse `RaiseException` em HTTP 400, sem estado
parcial — confirmado pelo teste de rollback (`test_procedures.py`), que verifica a contagem
de `atendimento` inalterada.

| | Trigger | Procedure |
| --- | --- | --- |
| Quem decide disparar | O evento de dado (INSERT/UPDATE/DELETE) | O cliente, explicitamente |
| Contornável por `UPDATE` direto no banco? | Não | N/A |
| Exemplos | `trg_check_sobreposicao_escala`, `trg_audita_atendimento`, `trg_atualiza_media_procedimentos` | `sp_registrar_atendimento_completo`, `sp_calcular_tempo_medio_espera`, `sp_reajustar_escala` |

## 2. Escolha da ORM: SQLAlchemy 2.0 async

O projeto usa `postgresql+psycopg://` (mesmo driver da Etapa 1, sem trocar para `asyncpg`)
sobre `AsyncEngine`/`AsyncSession`. A API 2.0 (`select()` como Core statement,
`Mapped`/`mapped_column` tipados, `async_sessionmaker`) permite escrever a DSL sem SQL
textual — `text()` só aparece para chamar as stored procedures, que são objetos de banco,
não tabelas — e sem abrir mão de transações declarativas e sessão com identity map. O
argumento decisivo, porém, é a herança nativa mapeando a especialização do DER.

**Herança joined sem coluna discriminadora.** `PESSOA → PACIENTE|PROFISSIONAL →
PRECEPTOR|RESIDENTE` (`docs/modelagem.md`, seção 3) é modelada com joined table
inheritance: `select(Pessoa)` já devolve instâncias resolvidas como `Paciente`,
`Preceptor` ou `Residente`, conforme a linha. É a evidência mais forte de que o ORM não é
só conveniência sobre `INSERT`/`SELECT`: expressa uma decisão de modelagem que o SQL cru
da Etapa 1 deixava implícita em `JOIN`s repetidos em cada repository. O desafio: o schema
não tem coluna discriminadora (contrato compartilhado com issues de banco em paralelo, não
podia ser alterado). A solução (`app/models/pessoa.py`) usa `polymorphic_on` com **qualquer
expressão SQL**, não só coluna física — um único `CASE` com subconsultas `EXISTS`
correlacionadas às quatro tabelas filhas:

```sql
CASE
    WHEN EXISTS (SELECT 1 FROM residente    WHERE residente.id_profissional = pessoa.id_pessoa)    THEN 'residente'
    WHEN EXISTS (SELECT 1 FROM preceptor    WHERE preceptor.id_profissional = pessoa.id_pessoa)    THEN 'preceptor'
    WHEN EXISTS (SELECT 1 FROM profissional WHERE profissional.id_pessoa    = pessoa.id_pessoa)    THEN 'profissional'
    WHEN EXISTS (SELECT 1 FROM paciente     WHERE paciente.id_pessoa        = pessoa.id_pessoa)    THEN 'paciente'
    ELSE 'pessoa'
END
```

As tabelas filhas são referenciadas via `table()`/`column()` do Core (só nome de
tabela/coluna), evitando import circular entre os módulos de agregado.

**Limitações**, documentadas no docstring do próprio módulo: (1) custo por linha — até 4
subconsultas `EXISTS` por consulta a `Pessoa`, aceitável no volume da disciplina, mas uma
coluna física seria O(1); (2) sem enforcement da disjunção — a `CASE` só decide qual classe
instanciar, não impede a mesma `id_pessoa` em `paciente` e `profissional` ao mesmo tempo
(lacuna já documentada desde a Etapa 1, seção 3.3 de `modelagem.md`); em conflito, a ordem
dos `WHEN` favorece profissional/residente/preceptor sobre paciente, desempate arbitrário;
(3) acoplamento por nome literal de tabela/coluna, não por FK — renomear quebra o
discriminador silenciosamente em runtime; (4) `with_polymorphic(Pessoa, "*")` é necessário
para eager load dos subtipos.

**O que se perdeu.** Controle fino do SQL gerado: na Etapa 1 cada repository escrevia
exatamente o `SELECT`/`JOIN` executado; agora o SQL efetivo emerge da combinação de
`relationship(lazy=...)` no modelo com as `options()` no ponto de consulta — uma camada de
indireção a mais sem inspecionar o log (`SQLALCHEMY_ECHO=1`). E o risco de N+1, o preço
mais concreto de mapear relacionamentos como atributos: `atendimento.py::list_by_paciente`
demonstra isso de propósito, com `lazyload()` desligando o eager padrão e `await
atendimento.awaitable_attrs.<rel>` dentro do loop gerando uma consulta extra por
atendimento — em contraste direto com `list_all` (`joinedload()` explícito) e
`list_procedimentos` (`selectinload()`). A estratégia de loading é uma decisão revisitada
em cada ponto de consulta, não algo que o ORM resolve por si.

**O que se ganhou.** Mapeamento explícito da especialização, como já discutido.
Transações declarativas: `async with session.begin(): session.add(residente)`
(`residente.py::create`) — como `Residente` fecha os três níveis da herança joined, uma
única instância adicionada à sessão emite três `INSERT`s na mesma transação; se o terceiro
falhar (`CHECK` de `ano_residencia`), o `ROLLBACK` automático desfaz os dois primeiros, sem
`BEGIN`/`COMMIT` manuais no repository. Consultas tipadas (`Mapped[int]`,
`Mapped["Residente"]`) dão checagem estática que SQL bruto em string nunca daria. E menos
código: a migração do CRUD (issue #8, PR #19) preservou os mesmos contratos de resposta com
saldo **negativo** de linhas nos repositories — a DSL composicional elimina o boilerplate
de abrir cursor, montar `JOIN`s manualmente e desserializar cada linha em dicionário, que o
SQL cru duplicava em cada função.

A troca vale a pena aqui porque o ganho central — expressar a especialização do DER como
hierarquia de classes, com o tipo concreto resolvido por linha — ataca uma dificuldade que
o SQL cru só contornava com `JOIN`s repetidos e nenhuma verificação estática. O custo
(indireção sobre o SQL gerado, disciplina para evitar N+1) é real e está documentado nos
próprios pontos do código onde aparece, não escondido.
